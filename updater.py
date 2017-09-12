import updater.main
import win32com.client
win32com.client.gencache.is_readonly=False

updater.main.Main()
