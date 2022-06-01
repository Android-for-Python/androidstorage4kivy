from kivy.logger import Logger
from kivy.app import App
from kivy.clock import mainthread
from kivy.core.window import Window
from android import activity, mActivity
from jnius import autoclass

Intent = autoclass('android.content.Intent')

# Source https://github.com/Android-for-Python/androidstorage4kivy

# Requires
# READ_EXTERNAL_STORAGE   Android < 10
# READ_EXTERNAL_STORAGE   Android >= 10 and file not owned by this app 

class Chooser():
    
    def __init__(self, callback = None, **kwargs):
        self.REQUEST_CODE_SINGLE = 42434445 
        self.REQUEST_CODE_MULTIPLE = 42434446 
        self.callback=callback
        
    def choose_content(self, MIME_type = '*/*', multiple = False):
        try:
            activity.bind(on_activity_result=self.intent_callback)
            App.get_running_app().bind(on_resume = self.begone_you_black_screen)
            self.intent = Intent(Intent.ACTION_GET_CONTENT)
            self.intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, multiple);
            REQUEST_CODE = self.REQUEST_CODE_SINGLE
            if multiple:
                REQUEST_CODE = self.REQUEST_CODE_MULTIPLE
            self.intent.setType(MIME_type)
            self.intent2 = Intent.createChooser(self.intent, None)
            mActivity.startActivityForResult(self.intent2, REQUEST_CODE)
        except Exception as e:
            Logger.warning('Chooser.choose_content():')
            Logger.warning(str(e))        

    def intent_callback(self, requestCode, resultCode, intent):
        activity.unbind(on_activity_result=self.intent_callback)
        if resultCode == -1: # Activity.RESULT_OK
            try:
                if intent and self.callback:
                    if requestCode == self.REQUEST_CODE_SINGLE:
                        self.callback([intent.getData()])
                    elif requestCode == self.REQUEST_CODE_MULTIPLE:
                        shared_file_list = []
                        data = intent.getData()
                        clipData = intent.getClipData()
                        if data:
                            shared_file_list.append(data)
                        elif clipData:
                            for i in range(clipData.getItemCount()):
                                shared_file = clipData.getItemAt(i).getUri()
                                shared_file_list.append(shared_file)
                        self.callback(shared_file_list)
            except Exception as e:
                Logger.warning('Chooser.intent_callback():')
                Logger.warning(str(e))        

    # On return from the Chooser this Kivy app sometimes has a black screen,
    # but its event loop is running.
    # This workaround is scheduled in choose_content() to occur on_resume
    @mainthread
    def begone_you_black_screen(self, arg):
        App.get_running_app().unbind(on_resume = self.begone_you_black_screen)
        Window.update_viewport()
                


    
