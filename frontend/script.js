// DOM Elements
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const titleEl = document.getElementById("title");
const summaryEl = document.getElementById("summary");
const stepsEl = document.getElementById("steps");
const smsEl = document.getElementById("sms_text");
const copySmsBtn = document.getElementById("copy_sms");
const fallbackInfo = document.getElementById("fallback-info");

// Offline fallback data
const FALLBACK_DATA = {
  earthquake: {
    title: "Earthquake Safety",
    summary: "If you're indoors during an earthquake, stay there. Move away from windows and heavy furniture. Drop, cover, and hold on.",
    steps: [
      "Drop to your hands and knees",
      "Cover your head and neck with your arms",
      "Hold on to any sturdy furniture until the shaking stops",
      "If in bed, stay there and cover your head with a pillow",
      "Stay indoors until the shaking stops and you're sure it's safe to exit"
    ],
    sms_template: "EARTHQUAKE ALERT! I'm at [LOCATION]. The building is shaking. Need immediate assistance. Please help!"
  },
  fire: {
    title: "Fire Emergency",
    summary: "In case of fire, remember to stay low to the ground and get out as quickly as possible.",
    steps: [
      "Get down low and crawl to the nearest exit",
      "Feel doors with the back of your hand before opening",
      "If smoke is present, use an alternate exit",
      "Meet at the designated meeting point",
      "Call emergency services once safe"
    ],
    sms_template: "FIRE ALERT! Fire at [LOCATION]. Need immediate assistance. Please send help!"
  },
  flood: {
    title: "Flood Safety",
    summary: "Move to higher ground immediately if you're in a flood-prone area. Do not walk through moving water.",
    steps: [
      "Move to higher ground immediately",
      "Avoid walking through moving water",
      "Do not drive into flooded areas",
      "Stay away from downed power lines",
      "Follow evacuation orders from local authorities"
    ],
    sms_template: "FLOOD ALERT! Trapped at [LOCATION]. Water levels rising. Need immediate assistance!"
  },
  tsunami: {
    title: "Tsunami Warning",
    summary: "If you're near the coast and feel a strong earthquake, move to higher ground immediately.",
    steps: [
      "Move to higher ground immediately",
      "Follow tsunami evacuation routes",
      "Do not go to the shore to watch the waves",
      "Stay away from the coast until authorities say it's safe",
      "Listen to emergency alerts for updates"
    ],
    sms_template: "TSUNAMI WARNING! At [LOCATION]. Moving to higher ground. Please check on me later."
  }
};

// Set online/offline status
function setOnline(online) {
  statusEl.textContent = online ? "ONLINE" : "OFFLINE";
  statusEl.className = online ? "status online" : "status offline";
}

// Initialize online status
setOnline(navigator.onLine);
window.addEventListener('online', () => setOnline(true));
window.addEventListener('offline', () => setOnline(false));

// Handle emergency button clicks
async function handleEmergency(type) {
  resultEl.classList.add("hidden");
  fallbackInfo.classList.add("hidden");
  
  try {
    // Try to get location
    const position = await getLocation();
    const location = position ? 
      `Lat: ${position.coords.latitude.toFixed(4)}, Long: ${position.coords.longitude.toFixed(4)}` : 
      "[LOCATION UNKNOWN]";
    
    // Try to send alert to server if online
    if (navigator.onLine) {
      try {
        const response = await fetch('/api/alert', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ type, location })
        });
        
        if (!response.ok) throw new Error('Server error');
        
        const data = await response.json();
        showResult(data, type, location);
        return;
      } catch (e) {
        console.warn('Failed to send alert to server, using fallback data', e);
      }
    }
    
    // If offline or server error, use fallback data
    fallbackInfo.classList.remove("hidden");
    showResult(FALLBACK_DATA[type], type, location);
    
  } catch (error) {
    console.error('Error handling emergency:', error);
    alert('Error processing your request. Please try again.');
  }
}

// Get current geolocation
function getLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }
    
    navigator.geolocation.getCurrentPosition(
      position => resolve(position),
      error => {
        console.warn('Geolocation error:', error);
        resolve(null);
      },
      { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
    );
  });
}

// Display the result
function showResult(data, type, location) {
  // Update the UI with the response data
  titleEl.textContent = data.title || `${type.charAt(0).toUpperCase() + type.slice(1)} Emergency`;
  summaryEl.textContent = data.summary || '';
  
  // Update steps
  stepsEl.innerHTML = '';
  const steps = data.steps || [];
  steps.forEach(step => {
    const li = document.createElement('li');
    li.textContent = step;
    stepsEl.appendChild(li);
  });
  
  // Update SMS template with location
  let smsText = data.sms_template || '';
  smsText = smsText.replace('[LOCATION]', location);
  smsEl.textContent = smsText;
  
  // Show the result section
  resultEl.classList.remove('hidden');
  
  // Scroll to result
  resultEl.scrollIntoView({ behavior: 'smooth' });
}

// Copy SMS to clipboard
copySmsBtn.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(smsEl.textContent);
    // Visual feedback
    const originalText = copySmsBtn.innerHTML;
    copySmsBtn.innerHTML = '<span class="material-symbols-outlined">check</span>';
    setTimeout(() => {
      copySmsBtn.innerHTML = originalText;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy text:', err);
    alert('Failed to copy SMS to clipboard');
  }
});

// Make handleEmergency globally available
window.handleEmergency = handleEmergency;
