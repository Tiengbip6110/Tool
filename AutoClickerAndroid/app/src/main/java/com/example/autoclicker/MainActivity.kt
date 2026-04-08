package com.example.autoclicker

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        findViewById<Button>(R.id.btn_accessibility).setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        findViewById<Button>(R.id.btn_overlay).setOnClickListener {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                if (!Settings.canDrawOverlays(this)) {
                    val intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:$packageName")
                    )
                    startActivityForResult(intent, 101)
                } else {
                    Toast.makeText(this, "Overlay permission already granted", Toast.LENGTH_SHORT).show()
                }
            }
        }

        findViewById<Button>(R.id.btn_single_mode).setOnClickListener {
            if (checkPermissions()) {
                startFloatingService(FloatingControlService.MODE_SINGLE)
                finish()
            }
        }

        findViewById<Button>(R.id.btn_multi_mode).setOnClickListener {
            if (checkPermissions()) {
                startFloatingService(FloatingControlService.MODE_MULTI)
                finish()
            }
        }
    }

    private fun checkPermissions(): Boolean {
        var hasPermissions = true

        if (AutoClickService.instance == null) {
            Toast.makeText(this, "Please enable Accessibility Service first", Toast.LENGTH_SHORT).show()
            hasPermissions = false
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this)) {
            Toast.makeText(this, "Please grant Overlay Permission", Toast.LENGTH_SHORT).show()
            hasPermissions = false
        }

        return hasPermissions
    }

    private fun startFloatingService(mode: Int) {
        val intent = Intent(this, FloatingControlService::class.java)
        intent.putExtra(FloatingControlService.EXTRA_MODE, mode)
        startService(intent)
    }
}
