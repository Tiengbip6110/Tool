package com.example.autoclicker

import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.PixelFormat
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.TextView

class FloatingControlService : Service() {

    private lateinit var windowManager: WindowManager
    private var controlView: View? = null
    private val targetViews = mutableListOf<View>()

    private var isPlaying = false
    private val handler = Handler(Looper.getMainLooper())
    private var clickDelay: Long = 1000 // default 1 second
    private var mode = MODE_SINGLE

    companion object {
        const val MODE_SINGLE = 1
        const val MODE_MULTI = 2
        const val EXTRA_MODE = "EXTRA_MODE"
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        mode = intent?.getIntExtra(EXTRA_MODE, MODE_SINGLE) ?: MODE_SINGLE
        windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager

        showControlView()

        if (mode == MODE_SINGLE) {
            addTargetView()
        }

        return START_STICKY
    }

    private fun showControlView() {
        if (controlView != null) return

        controlView = LayoutInflater.from(this).inflate(R.layout.layout_floating_control, null)

        val layoutParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            else
                WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 0
            y = 100
        }

        windowManager.addView(controlView, layoutParams)

        val btnPlayPause = controlView?.findViewById<Button>(R.id.btn_play_pause)
        val btnAdd = controlView?.findViewById<Button>(R.id.btn_add)
        val btnRemove = controlView?.findViewById<Button>(R.id.btn_remove)
        val btnClose = controlView?.findViewById<Button>(R.id.btn_close)

        if (mode == MODE_SINGLE) {
            btnAdd?.visibility = View.GONE
            btnRemove?.visibility = View.GONE
        }

        btnPlayPause?.setOnClickListener {
            if (isPlaying) {
                stopAutoClick()
                btnPlayPause.text = "Play"
            } else {
                startAutoClick()
                btnPlayPause.text = "Pause"
            }
        }

        btnAdd?.setOnClickListener {
            if (mode == MODE_MULTI) {
                addTargetView()
            }
        }

        btnRemove?.setOnClickListener {
            if (mode == MODE_MULTI && targetViews.isNotEmpty()) {
                val lastView = targetViews.removeLast()
                windowManager.removeView(lastView)
            }
        }

        btnClose?.setOnClickListener {
            stopSelf()
        }

        makeDraggable(controlView!!, layoutParams, isControlView = true)
    }

    private fun addTargetView() {
        val targetView = LayoutInflater.from(this).inflate(R.layout.layout_target_point, null)

        val index = targetViews.size + 1
        targetView.findViewById<TextView>(R.id.tv_target_number)?.text = index.toString()

        val layoutParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            else
                WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.CENTER
        }

        windowManager.addView(targetView, layoutParams)
        targetViews.add(targetView)

        makeDraggable(targetView, layoutParams, isControlView = false)
    }

    private fun makeDraggable(view: View, params: WindowManager.LayoutParams, isControlView: Boolean) {
        var initialX: Int = 0
        var initialY: Int = 0
        var initialTouchX: Float = 0f
        var initialTouchY: Float = 0f

        view.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = params.x
                    initialY = params.y
                    initialTouchX = event.rawX
                    initialTouchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    params.x = initialX + (event.rawX - initialTouchX).toInt()
                    params.y = initialY + (event.rawY - initialTouchY).toInt()
                    windowManager.updateViewLayout(view, params)
                    true
                }
                else -> false
            }
        }
    }

    private var currentTargetIndex = 0

    private val clickRunnable = object : Runnable {
        override fun run() {
            if (!isPlaying || targetViews.isEmpty()) return

            val target = targetViews[currentTargetIndex]
            val params = target.layoutParams as WindowManager.LayoutParams

            // Calculate absolute center using screen coordinates
            val loc = IntArray(2)
            target.getLocationOnScreen(loc)

            val x = (loc[0] + target.width / 2).toFloat()
            val y = (loc[1] + target.height / 2).toFloat()

            Log.d("FloatingControlService", "Clicking at $x, $y")
            AutoClickService.instance?.performClick(x, y, 50)

            if (mode == MODE_MULTI) {
                currentTargetIndex = (currentTargetIndex + 1) % targetViews.size
            }

            handler.postDelayed(this, clickDelay)
        }
    }

    private fun startAutoClick() {
        if (AutoClickService.instance == null) {
            Log.e("FloatingControlService", "AutoClickService is not running")
            return
        }
        isPlaying = true
        currentTargetIndex = 0
        handler.post(clickRunnable)
    }

    private fun stopAutoClick() {
        isPlaying = false
        handler.removeCallbacks(clickRunnable)
    }

    override fun onDestroy() {
        super.onDestroy()
        stopAutoClick()
        controlView?.let { windowManager.removeView(it) }
        targetViews.forEach { windowManager.removeView(it) }
        targetViews.clear()
    }
}
