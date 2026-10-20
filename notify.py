"""System (status-bar) notifications on Android through pyjnius. Every function is a no-op on a PC."""

from kivy.utils import platform

CHANNEL_ID = "ra_unlocks"


def available():
    return platform == "android"


def request_permission():
    """Android 13+ asks the user once for the right to show notifications."""
    if not available():
        return
    try:
        from android.permissions import request_permissions
        request_permissions(["android.permission.POST_NOTIFICATIONS"])
    except Exception as e:
        print("notify: permission request failed:", e)


def send(title, text, notif_id=1, channel_name="Achievements", channel_desc=""):
    """Show one notification (tapping it opens the app). Returns True when it was handed to Android."""
    if not available():
        return False
    try:
        from jnius import autoclass, cast
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        Context = autoclass("android.content.Context")
        String = autoclass("java.lang.String")
        Version = autoclass("android.os.Build$VERSION")
        Builder = autoclass("android.app.Notification$Builder")
        CharSequence = "java.lang.CharSequence"
        manager = activity.getSystemService(Context.NOTIFICATION_SERVICE)
        if Version.SDK_INT >= 26:
            NotificationChannel = autoclass("android.app.NotificationChannel")
            NotificationManager = autoclass("android.app.NotificationManager")
            channel = NotificationChannel(CHANNEL_ID, cast(CharSequence, String(channel_name)), NotificationManager.IMPORTANCE_DEFAULT)
            channel.setDescription(channel_desc)
            manager.createNotificationChannel(channel)
            builder = Builder(activity, CHANNEL_ID)
        else:
            builder = Builder(activity)
        builder.setSmallIcon(activity.getApplicationInfo().icon)
        builder.setContentTitle(cast(CharSequence, String(title)))
        builder.setContentText(cast(CharSequence, String(text)))
        builder.setAutoCancel(True)
        Intent = autoclass("android.content.Intent")
        PendingIntent = autoclass("android.app.PendingIntent")
        intent = Intent(activity.getApplicationContext(), PythonActivity)
        intent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP)
        flags = PendingIntent.FLAG_UPDATE_CURRENT | (PendingIntent.FLAG_IMMUTABLE if Version.SDK_INT >= 23 else 0)
        builder.setContentIntent(PendingIntent.getActivity(activity, 0, intent, flags))
        manager.notify(int(notif_id), builder.build())
        return True
    except Exception as e:
        print("notify: could not show the notification:", e)
        return False
