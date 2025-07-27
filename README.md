# JellySkip - Netflix-Style Auto-Skip for Jellyfin
**Status: Proof of Concept / Vibe Coded** 🔬

JellySkip is a Kodi service addon that adds Netflix-style countdown functionality to Jellyfin media playback. This started as a simple intro skip addon and evolved into something more ambitious through iterative "vibe coding" sessions.

**⚠️ Transparency**: This is very much a proof of concept that was developed through experimental coding sessions. While it works well in testing, it hasn't been through rigorous production development practices. The goal is to eventually contribute this functionality to the main Jellyfin-Kodi project.

## What Actually Works (Tested Functionality)

### ✅ Netflix-Style Countdown
- Countdown dialog appears during outro segments
- Shows next episode info: "Next: S03E11 - Episode Title"  
- 15-second countdown with "Play Now" and "Cancel" buttons
- Auto-advances to next episode when timer expires
- Positioned in bottom-right corner like Netflix

### ✅ Settings Integration  
- Modern Kodi Matrix settings format
- Enable/disable countdown functionality
- Configurable countdown duration (5-30 seconds)
- Toggle auto-advance behavior
- Works alongside existing intro skip

### ✅ Preserved Original Functionality
- Traditional intro skip button (original JellySkip behavior)
- All existing segment detection capabilities

<details> 
  <summary>Original Skip Button (still works)</summary>
    <img src="https://i.imgur.com/hL62YyN.png" alt="Original skip button"/>
</details>

## Current Limitations & "Vibe Coded" Aspects

### 🔧 Known Issues
- **Limited testing environments**: Primarily tested on CoreELEC with specific Jellyfin setup
- **Error handling**: Basic fallbacks implemented, but edge cases likely exist  
- **UI responsiveness**: Dialog positioning may need tweaks on different screen resolutions
- **Code organization**: Functional but could benefit from more structured architecture

### 🎯 "Proof of Concept" Status
- **Rapid iteration**: Features added through experimental development sessions
- **Minimal testing**: Works in my environment, but broader compatibility unknown
- **Documentation**: Added retroactively, may not cover all scenarios
- **Performance**: No optimization or performance testing conducted

## Requirements

- **Kodi Matrix (19.0+)** (tested on Kodi 21.2)
- **Jellyfin Server 10.10.0+** with Media Segments API
- **Jellyfin intro-skipper plugin** ([intro-skipper](https://github.com/intro-skipper/intro-skipper))
- **Jellyfin-Kodi addon** installed and configured

## Installation (Use at Your Own Risk)

### For Testing/Development
```bash
git clone https://github.com/YOUR_USERNAME/service.jellyskip.git
cd service.jellyskip

# Option 1: Manual installation
# Copy to: ~/.kodi/addons/service.jellyskip (Linux/Mac)
# Copy to: %APPDATA%\Kodi\addons\service.jellyskip (Windows)

# Option 2: Use deployment script (CoreELEC/LibreELEC)
chmod +x deploy-to-coreelec.sh
./deploy-to-coreelec.sh
