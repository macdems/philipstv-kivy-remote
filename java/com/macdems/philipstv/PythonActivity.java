package com.macdems.philipstv;

import android.view.KeyEvent;
import org.libsdl.app.SDLActivity;


public class PythonActivity extends org.kivy.android.PythonActivity {

    @Override
    public boolean dispatchKeyEvent(KeyEvent event) {
        int action = event.getAction();
        int keyCode = event.getKeyCode();
        switch (keyCode) {
            case KeyEvent.KEYCODE_VOLUME_UP:
            case KeyEvent.KEYCODE_VOLUME_DOWN:
                if (action == KeyEvent.ACTION_DOWN) {
                SDLActivity.onNativeKeyDown(keyCode);
                } else if (action == KeyEvent.ACTION_UP) {
                SDLActivity.onNativeKeyUp(keyCode);
                }
                return true;
            default:
                return super.dispatchKeyEvent(event);
        }
    }
}
