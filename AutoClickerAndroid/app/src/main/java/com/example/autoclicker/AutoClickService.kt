package com.example.autoclicker

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Intent
import android.graphics.Path
import android.util.Log
import android.view.accessibility.AccessibilityEvent

class AutoClickService : AccessibilityService() {

    companion object {
        var instance: AutoClickService? = null
            private set
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.d("AutoClickService", "Service Connected")
    }

    override fun onUnbind(intent: Intent?): Boolean {
        instance = null
        Log.d("AutoClickService", "Service Unbound")
        return super.onUnbind(intent)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Not used, but required to be implemented
    }

    override fun onInterrupt() {
        Log.d("AutoClickService", "Service Interrupted")
    }

    fun performClick(x: Float, y: Float, duration: Long) {
        val path = Path()
        path.moveTo(x, y)
        val builder = GestureDescription.Builder()
        val strokeDescription = GestureDescription.StrokeDescription(path, 0, duration)
        builder.addStroke(strokeDescription)

        val gesture = builder.build()
        val result = dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                super.onCompleted(gestureDescription)
                Log.d("AutoClickService", "Gesture completed")
            }

            override fun onCancelled(gestureDescription: GestureDescription?) {
                super.onCancelled(gestureDescription)
                Log.d("AutoClickService", "Gesture cancelled")
            }
        }, null)

        Log.d("AutoClickService", "Dispatch result: $result for coordinates ($x, $y)")
    }
}
