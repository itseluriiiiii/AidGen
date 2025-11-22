import logging
from datetime import datetime

from vonage import Auth, HttpClientOptions, Vonage
from vonage_sms import SmsMessage

from ..config import config

# Configure logging
logger = logging.getLogger(__name__)

class SOSService:
    def __init__(self):
        """Initialize the SOS service for outbound SMS."""
        self.default_contacts = self._parse_emergency_contacts(
            config.SOS_EMERGENCY_CONTACTS
        )
        self._vonage_client = None
        self._sms_client = None
        missing_vars = [
            var for var in [
                'VONAGE_API_KEY',
                'VONAGE_API_SECRET',
                'VONAGE_FROM_NUMBER',
                'VONAGE_API_URL'
            ]
            if not getattr(config, var)
        ]
        if missing_vars:
            logger.warning("Missing Vonage configuration: %s", ", ".join(missing_vars))
        else:
            try:
                auth = Auth(api_key=config.VONAGE_API_KEY, api_secret=config.VONAGE_API_SECRET)
                http_options = HttpClientOptions(api_server=config.VONAGE_API_URL)
                self._vonage_client = Vonage(auth=auth, http_client_options=http_options)
                self._sms_client = self._vonage_client.sms
            except Exception as exc:
                logger.error("Failed to initialize Vonage client: %s", exc)

        logger.info("SOS service initialized for Vonage SMS")

    @staticmethod
    def _parse_emergency_contacts(value: str):
        """Parse SOS_EMERGENCY_CONTACTS env var into a list of contact dicts."""
        contacts = []
        for raw in (value or '').split(','):
            raw = raw.strip()
            if not raw:
                continue
            if ':' not in raw:
                continue
            name, phone = raw.split(':', 1)
            name = name.strip() or 'Emergency Contact'
            phone = phone.strip()
            if not phone:
                continue
            contacts.append({'name': name, 'phone': phone})
        return contacts

    def send_emergency_sms(
        self,
        emergency_type,
        latitude=None,
        longitude=None,
        location_desc=None,
        emergency_contacts=None
    ):
        """
        Send emergency SMS with location to all emergency contacts

        Args:
            emergency_type: Type of emergency (e.g., "EARTHQUAKE", "FIRE")
            latitude: User's latitude
            longitude: User's longitude
            emergency_contacts: List of dicts with 'name' and 'phone' keys

        Returns:
            dict with status and message details
        """
        contacts = emergency_contacts or self.default_contacts
        if not contacts:
            error_msg = 'No emergency contacts configured for SOS alerts.'
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

        if not self._sms_client:
            error_msg = 'Vonage client is not configured. Check API credentials.'
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        lines = [f"🚨 EMERGENCY ALERT - {emergency_type.upper()} 🚨", '',
                 "I need immediate help! I'm experiencing an emergency.", '']
        maps_link = None

        if latitude is not None and longitude is not None:
            lines.append('📍 My Location:')
            lines.append(f"Latitude: {latitude:.6f}")
            lines.append(f"Longitude: {longitude:.6f}")
            maps_link = (
                f"https://www.google.com/maps/dir/?api=1&destination="
                f"{latitude},{longitude}"
            )
            lines.extend(['', '🗺️ Get Directions:', maps_link])
        elif location_desc:
            lines.append('📍 My Location:')
            lines.append(location_desc)
        else:
            lines.append('📍 My Location: [LOCATION UNAVAILABLE]')

        lines.extend(['', f"⏰ Time: {timestamp}", '', 'Please send help immediately!'])
        message_body = ' '.join(line.strip() for line in lines if line.strip())

        results = []

        # Send SMS to each emergency contact
        for contact in contacts:
            try:
                sms_message = SmsMessage(
                    from_=config.VONAGE_FROM_NUMBER,
                    to=contact['phone'].lstrip('+'),
                    text=message_body
                )
            except Exception as exc:
                logger.error(
                    "Invalid SMS payload for %s (%s): %s",
                    contact['name'],
                    contact['phone'],
                    exc
                )
                results.append({
                    'contact': contact['name'],
                    'phone': contact['phone'],
                    'status': 'failed',
                    'error': f'Invalid payload: {exc}'
                })
                continue
            try:
                response = self._sms_client.send(sms_message)
                messages = response.messages if hasattr(response, 'messages') else []
                if not messages:
                    raise ValueError('Vonage SMS response missing messages payload')

                message = messages[0]
                if message.status != '0':
                    error_text = getattr(message, 'error_text', 'Unknown Vonage error')
                    logger.error(
                        "Vonage API error for %s (%s): %s",
                        contact['name'],
                        contact['phone'],
                        error_text
                    )
                    results.append({
                        'contact': contact['name'],
                        'phone': contact['phone'],
                        'status': 'failed',
                        'error': error_text,
                        'response': response.model_dump()
                    })
                    continue

                results.append({
                    'contact': contact['name'],
                    'phone': contact['phone'],
                    'status': 'sent',
                    'response': response.model_dump()
                })
            except Exception as exc:
                logger.error(
                    "Vonage SMS send failed for %s (%s): %s",
                    contact['name'],
                    contact['phone'],
                    exc
                )
                results.append({
                    'contact': contact['name'],
                    'phone': contact['phone'],
                    'status': 'failed',
                    'error': str(exc)
                })

        # Check if all messages sent successfully
        all_sent = all(r['status'] == 'sent' for r in results)

        return {
            'success': all_sent,
            'message': 'All emergency alerts sent' if all_sent else 'Some alerts failed',
            'results': results,
            'location': {
                'latitude': latitude,
                'longitude': longitude,
                'maps_link': maps_link
            },
            'timestamp': timestamp
        }

    def send_whatsapp_emergency(self, *args, **kwargs):
        raise NotImplementedError("WhatsApp alerts no longer supported")