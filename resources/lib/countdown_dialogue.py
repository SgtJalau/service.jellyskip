import xbmcgui
import xbmc
import xbmcaddon
import threading
import time
from typing import Optional

class CountdownDialogue(xbmcgui.WindowXMLDialog):
    """Netflix-style countdown dialog for credits/outro segments"""
    
    # Control IDs
    PLAY_NOW_BUTTON_ID = 3003
    CANCEL_BUTTON_ID = 3004
    NEXT_EPISODE_LABEL_ID = 3002
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addon = xbmcaddon.Addon()
        
        # Dialog parameters
        self.countdown_duration = kwargs.get('countdown_duration', 15)
        self.next_episode_title = kwargs.get('next_episode_title', 'Next Episode')
        self.auto_advance = kwargs.get('auto_advance', True)
        
        # State management
        self.countdown_thread: Optional[threading.Thread] = None
        self.should_stop = False
        self.user_action = None
        self.remaining_time = self.countdown_duration
        
        xbmc.log("[JELLYSKIP] CountdownDialogue initialized successfully", xbmc.LOGINFO)
        
    def onInit(self):
        """Initialize the dialog when it opens"""
        try:
            # Set next episode label - exactly like mockup
            display_text = f"Next: {self.next_episode_title}"
            self.getControl(self.NEXT_EPISODE_LABEL_ID).setLabel(display_text)
            xbmc.log(f"[JELLYSKIP] Set episode label: {display_text}", xbmc.LOGINFO)
            
            # Set initial button text with countdown
            self._update_button_text()
            
            # Set focus to Play Now button (default)
            self.setFocus(self.getControl(self.PLAY_NOW_BUTTON_ID))
            
            # Start countdown
            self.start_countdown()
            
        except Exception as e:
            xbmc.log(f"[JELLYSKIP] CountdownDialogue.onInit error: {e}", xbmc.LOGERROR)
            
    def onClick(self, controlId):
        """Handle button clicks"""
        xbmc.log(f"[JELLYSKIP] CountdownDialogue onClick: {controlId}", xbmc.LOGINFO)
        
        if controlId == self.PLAY_NOW_BUTTON_ID:
            self.user_action = 'play_now'
            self.stop_countdown()
            self.close()
        elif controlId == self.CANCEL_BUTTON_ID:
            self.user_action = 'cancel'
            self.stop_countdown()
            self.close()
            
    def onAction(self, action):
        """Handle remote control actions - exactly like mockup"""
        action_id = action.getId()
        
        if action_id in [xbmcgui.ACTION_NAV_BACK, xbmcgui.ACTION_PREVIOUS_MENU]:
            # Escape key behavior
            self.user_action = 'cancel'
            self.stop_countdown()
            self.close()
        elif action_id == xbmcgui.ACTION_SELECT_ITEM:
            # Enter key behavior - activate focused button
            try:
                focused_control = self.getFocusId()
                if focused_control == self.PLAY_NOW_BUTTON_ID:
                    self.user_action = 'play_now'
                    self.stop_countdown()
                    self.close()
                elif focused_control == self.CANCEL_BUTTON_ID:
                    self.user_action = 'cancel'
                    self.stop_countdown()
                    self.close()
            except:
                # Fallback to play_now if focus detection fails
                self.user_action = 'play_now'
                self.stop_countdown()
                self.close()
        else:
            # Let parent handle navigation (arrow keys, etc.)
            super().onAction(action)
            
    def start_countdown(self):
        """Start the countdown timer"""
        self.countdown_thread = threading.Thread(target=self._countdown_worker)
        self.countdown_thread.daemon = True
        self.countdown_thread.start()
        
    def stop_countdown(self):
        """Stop the countdown timer"""
        self.should_stop = True
        if self.countdown_thread and self.countdown_thread.is_alive():
            self.countdown_thread.join(timeout=1.0)
            
    def _update_button_text(self):
        """Update the button text with current countdown - exactly like mockup"""
        try:
            button_text = f"Play Now ({self.remaining_time})"
            self.getControl(self.PLAY_NOW_BUTTON_ID).setLabel(button_text)
            xbmc.log(f"[JELLYSKIP] Updated button text: {button_text}", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"[JELLYSKIP] Error updating button text: {e}", xbmc.LOGERROR)
            
    def _countdown_worker(self):
        """Worker thread for countdown timer - exactly like mockup timing"""
        try:
            while self.remaining_time > 0 and not self.should_stop:
                self._update_button_text()
                time.sleep(1)  # 1-second intervals like mockup
                self.remaining_time -= 1
                
            # Handle countdown completion - auto-advance like mockup
            if not self.should_stop and self.auto_advance:
                xbmc.log("[JELLYSKIP] Countdown completed - auto advancing", xbmc.LOGINFO)
                self.user_action = 'timeout'
                self.close()
                
        except Exception as e:
            xbmc.log(f"[JELLYSKIP] Countdown worker error: {e}", xbmc.LOGERROR)
