Android Shared Storage 4 Kivy
=============================

*A package for accessing Android Shared Storage.*

## Overview

To use, add `androidstorage4kivy` to Buildozer requirements, see the examples.

### Programming Model

The methods in this Python package provide a consistent file storage model and api across Android versions >= 5. As a result the model implements constraints that may not exist on some older versions of Android. 

**The model consists of 'private files' which are accessed as traditional OS files, and 'shared files' which are copied or deleted by the api. 'Shared files' can be shared between apps in the usual Android ways, 'private files' cannot be shared between apps.** 

On Android shared storage is structured as collections (`Environment.DIRECTORY_MUSIC`,`Environment.DIRECTORY_DOCUMENTS`, etc.) that each hold specific file types. Android documents the [predefined collections](https://developer.android.com/reference/android/os/Environment).

### Classes

This package contains three classes, `SharedStorage`, `ShareSheet`, and `Chooser`. 

 - `SharedStorage` allows copying files to and from shared storage with the `copy_to_shared()`, `copy_from_shared()`, and `delete_shared()` methods.

 - `ShareSheet` allows sending plain text, or a 'shared file' to another app. Using the `share_plain_text()`, `share_file()`, and `share_file_list()` methods, these create an Android ShareSheet used to select the target app.

 - `Chooser` allows selecting a 'shared file' using the Android Chooser UI. The callback returns a list of one or more shared files.

These classes are described in more detail in the following sections.

On Android a 'shared file' is usually (but not always) implemented as an `'android.net.Uri'`, this is **not** a Python file reference. Which is why we copy between shared and private files (which are Python files). For consistent behavior across Android versions use only this api to create, consume, or delete a 'shared file'.

External storage must be availaible, this may not be true on older devices with a removable sdcard.

### Permissions

 - Android < 10 : WRITE_EXTERNAL_STORAGE 
 - Android >= 10 : READ_EXTERNAL_STORAGE required only to copy or list a 'shared file' not owned by this app. Except in Downloads where this permission does not apply.

### Examples

 - Basic usage, [shared_storage_example](https://github.com/Android-for-Python/shared_storage_example).

 - Share with another app, [share_send_example](https://github.com/Android-for-Python/share_send_example).

 - Receive from another app, [share_receive_example](https://github.com/Android-for-Python/share_receive_example).

## SharedStorage Class

### Overview

Use for copying files to and from shared storage, and deleting from shared storage.

The SharedStorage Class provides these methods: `copy_to_shared()`, `copy_from_shared()`, `delete_shared()`

### API  

```
 def copy_to_shared(private_file, collection = None, filepath = None)
     returns shared_file or None

 def copy_from_shared(shared_file)
     returns private_file or None

 def delete_shared(shared_file)
     returns True if deleted, else False
```

  `private_file` - a fully qualified file path to a file in app private storage; `copy_from_shared()` copies to app private cache storage.

  `collection` - override the default collection. Must be valid for the file type. For example .jpg (defaults to DIRECTORY_PICTURES) and can be DIRECTORY_DCIM, but not DIRECTORY_MOVIES. Invalid entries are ignored and the default is used.
 
  `filepath`  - shared storage filepath including file name, but not including 'Collection/app-Title'.

  `shared_file`  - A reference to a file in shared storage returned by `copy_to_shared()`. Or a string  e.g. '<collection>/<app-Title>/sub_dir/name.ext'. 


### Implementation Details

MediaStore file versions (" (N)" inserted the file name) are usually not created. However when a file cannot be replaced (due to some internal permissions issue that reqires MANAGER permission to adddress) a new file version will be added. Use the File Manager app (which has MANAGER permission) to address the underlying issue.

Some MIME classifications (on which Collection classification is based) have changed with Android versions. For example '.ogg' files are 'application/ogg' on older devices and 'audio/ogg' on newer devices.  

A share receive of a large file (such as an mp4) is slow on Android < 10. To improve performance of this case, copy the `faster_copy` directory in [share_receive_example](https://github.com/Android-for-Python/share_receive_example) to your app and in buildozer.spec add `android.add_src = faster_copy`.

The Downloads directory is a special case. In this directory Android only allows access to files downloaded by the current app. The traditional common usage of Downloads as a shared pool of files is not possible. 

## ShareSheet Class

### Overview

Enables sending either plain_text, a file, or a file list to another app. The target app is selected either with the ShareSheet UI, or specified with the api argument. Android requires that the target app must declare that it is able to receive shares of this type, for more details see the [share_receive_example](https://github.com/Android-for-Python/share_receive_example).

### API

```
    def share_plain_text(self, plain_text, app = None):
    
    def share_file(self, shared_file, app = None):

    def share_file_list(self, shared_file_list, app = None):
```

`plain_text` is a string.
	
`app` a string identifying the target app (for example, 'com.google.android.gm' for Gmail), The default opens a ShareSheet to select a compatible app.

`shared_file` is a file in shared storage.

`shared_file_list` is a list of files in shared storage.

### Android < 10

The ShareSheet class should probably be persistent since destroying the class destroys the shared uri. 

## Chooser Class

### Overview

The Chooser class enables opening an Android Chooser, the chosen 'shared file' or 'shared files' is returned in a callback. 

### API

Instantiate the class with a callback method as the argument.

```
       self.chooser = Chooser(self.chooser_callback)
```

The Chooser UI is opened with `choose_content()`, this can optionally be filtered by MIME type. The Android Chooser recognizes MIME wildcards such as 'image/\*' or '\*/\*' but not '\*/jpg'.  

```
       self.chooser.choose_content('video/*')
```
The selected files are reported by the app's callback method as a list. The default is one file in the list. To enable selecting multiple files, set `multiple = True`.
```
       self.chooser.choose_content('image/*', multiple = True)
```

```
   def chooser_callback(self, shared_file_list):
       self.private_files = []
       ss = SharedStorage()
       for shared_file in shared_file_list:
           self.private_files.append(ss.copy_from_shared(shared_file))
```



