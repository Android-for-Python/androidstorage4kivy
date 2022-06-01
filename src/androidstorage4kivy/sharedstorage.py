from kivy.logger import Logger
from android import mActivity, autoclass, cast, api_version
from os.path import splitext,join, basename, exists
from os import mkdir, remove 
from shutil import copyfile

FileOutputStream = autoclass('java.io.FileOutputStream')
FileInputStream = autoclass('java.io.FileInputStream')
Environment = autoclass('android.os.Environment')
MediaStoreMediaColumns = autoclass('android.provider.MediaStore$MediaColumns')
ContentUris = autoclass('android.content.ContentUris')
MimeTypeMap = autoclass('android.webkit.MimeTypeMap')
StreamCopy = None
if api_version > 28:
    FileUtils        = autoclass('android.os.FileUtils')
    MediaStoreFiles = autoclass('android.provider.MediaStore$Files')
    MediaStoreDownloads = autoclass('android.provider.MediaStore$Downloads')
    MediaStoreAudioMedia = autoclass('android.provider.MediaStore$Audio$Media')
    MediaStoreImagesMedia =autoclass('android.provider.MediaStore$Images$Media')
    MediaStoreVideoMedia = autoclass('android.provider.MediaStore$Video$Media')
    ContentValues = autoclass('android.content.ContentValues')
else:
    try:
        StreamCopy = autoclass('org.kivy.sharedstorage.StreamCopy')
    except:
        pass

# Source https://github.com/Android-for-Python/androidsatorage4kivy


class SharedStorage:

    ###################
    # Public methods
    ###################

    def copy_to_shared(self, private_file, collection = None, filepath = None):
        if private_file == None or not exists(private_file):
            return None
        file_name = basename(private_file)
        MIME_type = self.get_file_MIME_type(file_name)
        auto_collection = self._get_auto_collection(MIME_type)
        if not self._legal_collection(auto_collection, collection):
            collection = auto_collection
        path = [collection, self.get_app_title()]
        if filepath:
            sfp = filepath.split('/')
            file_name = sfp[-1]
            for f in sfp[:-1]:
                path.append(f)

        if api_version > 28:
            sub_directory = ''
            for d in path:
                sub_directory = join(sub_directory,d)
            uri = self._get_uri(join(sub_directory, file_name))
            context = mActivity.getApplicationContext()
            try:
                cr =  context.getContentResolver()
                ws = None
                if uri:
                    try:
                        ws  = cr.openOutputStream(uri,"rwt")
                    except:
                        Logger.info('File replace permission not granted.')
                        Logger.info('A new file version will be created.')
                        uri = None
                if not ws:
                    cv = ContentValues()
                    cv.put(MediaStoreMediaColumns.DISPLAY_NAME, file_name)
                    cv.put(MediaStoreMediaColumns.MIME_TYPE, MIME_type)  
                    cv.put(MediaStoreMediaColumns.RELATIVE_PATH, sub_directory)
                    root_uri = self._get_root_uri(path[0], MIME_type)
                    uri = cr.insert(root_uri, cv)
                    ws  = cr.openOutputStream(uri)
                # copy file contents
                rs = FileInputStream(private_file)
                FileUtils.copy(rs,ws) 
                ws.flush()
                ws.close()
                rs.close()
            except Exception as e:
                Logger.warning('SharedStorage.copy_to_shared():')
                Logger.warning(str(e))
                uri = None
            return uri
        else:
            root_directory = self._get_legacy_storage_location()
            if root_directory == None:
                return None
            sub_directory = root_directory
            for d in path:
                sub_directory = join(sub_directory,d) 
                if not exists(sub_directory):
                    mkdir(sub_directory)
            public_path = join(sub_directory, file_name)
            self.delete_shared(public_path)
            copyfile(private_file, public_path)
            return public_path

    
    def copy_from_shared(self, shared_file):
        if shared_file == None:
            return None
        if api_version > 28:
            uri = self._get_uri(shared_file)
            cache_file = self._copy_uri_to_cache(uri)
        else:
            if type(shared_file) == str:
                cache_file = self._copy_file_to_cache(shared_file)
            else:
                cache_file = self._copy_uri_to_cache(shared_file)
        return cache_file

    def delete_shared(self, shared_file):
        if shared_file == None:
            return False
        if api_version > 28 or type(shared_file) == 'android.net.Uri':
            uri = self._get_uri(shared_file)
            if not uri:
                return False
            context = mActivity.getApplicationContext()
            try:
                return context.getContentResolver().delete(uri,None,None) == 1
            except:
                Logger.info('File delete permission not granted, ignored.')
                return False
        elif type(shared_file) == str:
            path = join(self._get_legacy_storage_location(), shared_file)
            if exists(path):
                remove(path)
                return True
        return False


    ###################
    # Public utilities
    ###################

    def get_cache_dir(self):
        context = mActivity.getApplicationContext()
        result =  context.getExternalCacheDir()
        if not result:
            return None
        new_file_loc =  str(result.toString())
        if not new_file_loc:
            return None
        new_file_loc = join(new_file_loc,"FromSharedStorage")
        if not exists(new_file_loc):
            mkdir(new_file_loc)
        return new_file_loc
    
    def get_app_title(self):
        context = mActivity.getApplicationContext()
        appinfo = context.getApplicationInfo()
        if appinfo.labelRes:
            name = context.getString(appinfo.labelRes)
        else:
            name = appinfo.nonLocalizedLabel.toString()
        return name

    def get_file_MIME_type(self,file_name):
        MIME_type = 'application/unknown' 
        try :
            file_ext_no_dot = ''
            file_ext = splitext(file_name)[1]
            if file_ext:
                file_ext_no_dot = file_ext[1:]
            if file_ext_no_dot:
                lower_ext  = file_ext_no_dot.lower()
                mtm = MimeTypeMap.getSingleton()
                MIME_type = mtm.getMimeTypeFromExtension(lower_ext)
                if not MIME_type:
                    MIME_type = 'application/' + file_ext_no_dot
        except Exception as e:
            Logger.warning('SharedStorage.get_file_MIME_type():')
            Logger.warning(str(e))
        return MIME_type    

    ###################
    # Private utilities
    ###################

    def _get_auto_collection(self, MIME_type):
        root, ext = MIME_type.split('/')
        root = root.lower()
        if root == 'image':
            root_dir = Environment.DIRECTORY_PICTURES
        elif root == 'video':
            root_dir = Environment.DIRECTORY_MOVIES
        elif root == 'audio':
            root_dir = Environment.DIRECTORY_MUSIC
        else:
            root_dir = Environment.DIRECTORY_DOCUMENTS
        return root_dir

    def _get_root_uri(self, root_directory, MIME_type):
        if root_directory == Environment.DIRECTORY_DOWNLOADS:
            root_uri = MediaStoreDownloads.EXTERNAL_CONTENT_URI
        else:
            root, ext = MIME_type.split('/')
            root = root.lower()
            if root == 'image':
                root_uri = MediaStoreImagesMedia.EXTERNAL_CONTENT_URI
            elif root == 'video':
                root_uri = MediaStoreVideoMedia.EXTERNAL_CONTENT_URI
            elif root == 'audio':
                root_uri = MediaStoreAudioMedia.EXTERNAL_CONTENT_URI
            else:
                root_uri = MediaStoreFiles.getContentUri('external')
        return root_uri

    def _get_uri(self, shared_file):
        if type(shared_file) == str:
            shared_file = shared_file
            if 'file://' in shared_file or 'content://' in shared_file:
                return None
        else:
            uri = cast('android.net.Uri',shared_file)
            try:
                if uri.getScheme().lower() == 'content':
                    return uri
                else:
                    return None
            except:
                return None

        file_name = basename(shared_file)
        MIME_type = self.get_file_MIME_type(file_name)
        path = shared_file.split('/')
        if len(path) < 1:
            return None
        root = path[0]
            
        self.selection = MediaStoreMediaColumns.DISPLAY_NAME+"=? AND " 
        if api_version > 28:
            location = ''
            for d in path[:-1]:
                location = join(location,d)
            self.selection = self.selection +\
                MediaStoreMediaColumns.RELATIVE_PATH+"=?" 
            self.args = [file_name, location+'/']
        else:
            self.selection = self.selection + MediaStoreMediaColumns.DATA+"=?"
            self.args = [file_name, shared_file]

        root_uri = self._get_root_uri(root, MIME_type)
        context = mActivity.getApplicationContext()
        cursor = context.getContentResolver().query(root_uri, None,
                                                    self.selection,
                                                    self.args, None)
        fileUri = None
        if cursor:
            while cursor.moveToNext():
                dn = MediaStoreMediaColumns.DISPLAY_NAME
                index = cursor.getColumnIndex(dn)
                fileName = cursor.getString(index)
                if file_name == fileName:
                    id_index = cursor.getColumnIndex(MediaStoreMediaColumns._ID)
                    id = cursor.getLong(id_index)
                    fileUri = ContentUris.withAppendedId(root_uri,id)
                    break
            cursor.close()
        return fileUri

    def _copy_uri_to_cache(self, uri):
        if not uri:
            return uri
        uri = cast('android.net.Uri',uri)
        if uri.getScheme().lower() == 'file':
            return self._copy_file_to_cache(uri.getPath())
        context = mActivity.getApplicationContext()
        cursor = context.getContentResolver().query(uri, None,
                                                    None, None, None)
        if not cursor:
            return None
        dn = MediaStoreMediaColumns.DISPLAY_NAME
        nameIndex = cursor.getColumnIndex(dn)
        cursor.moveToFirst()
        file_name = cursor.getString(nameIndex)
        cache_dir = self.get_cache_dir()
        if not cache_dir:
            return None
        cache_file= join(cache_dir, file_name)
        if exists(cache_file):
            remove(cache_file)
        cr = context.getContentResolver()
        try:
            rs = cr.openInputStream(uri)
            ws = FileOutputStream(cache_file)
            if api_version > 28:
                # fastest
                FileUtils.copy(rs,ws)
            elif StreamCopy:
                # pretty fast
                StreamCopy(rs, ws) 
            else:
                # slow
                jbytes = bytearray(2048)
                while True:
                    num = rs.read(jbytes) 
                    if num == -1:
                        break
                    ws.write(jbytes, 0, num)
            ws.close()
            rs.close()
        except Exception as e:
            Logger.warning('SharedStorage._copy_uri_to_cache():')
            Logger.warning(str(e))
        cursor.close()
        return cache_file

    def _copy_file_to_cache(self, shared_file):
        path = join(self._get_legacy_storage_location(), shared_file)
        cache_file = None
        if exists(path):
            cache_dir = self.get_cache_dir()
            if not cache_dir:
                return None
            cache_file = join(cache_dir, basename(path))
            copyfile(path, cache_file)
        return cache_file

    def _get_legacy_storage_location(self):
        root = Environment.getExternalStorageDirectory()
        root_dir = str(root.getAbsolutePath())
        if exists(root_dir):
            return root_dir
        return None

    def _legal_collection(self, auto_collection, collection):
        # Too many rules, dudes.
        if collection == None:
            return False
        elif collection == Environment.DIRECTORY_DOWNLOADS:
            return True
        elif auto_collection == Environment.DIRECTORY_MUSIC:
            return collection in [Environment.DIRECTORY_ALARMS,
                                  Environment.DIRECTORY_AUDIOBOOKS,
                                  Environment.DIRECTORY_MUSIC,
                                  Environment.DIRECTORY_NOTIFICATIONS,
                                  Environment.DIRECTORY_PODCASTS,
                                  Environment.DIRECTORY_RECORDINGS,
                                  Environment.DIRECTORY_RINGTONES]
        elif auto_collection == Environment.DIRECTORY_PICTURES:
            return collection in [Environment.DIRECTORY_DCIM,
                                  Environment.DIRECTORY_PICTURES,
                                  Environment.DIRECTORY_SCREENSHOTS]
        elif auto_collection == Environment.DIRECTORY_MOVIES:
            return collection in [Environment.DIRECTORY_MOVIES]
        return collection in [Environment.DIRECTORY_DOCUMENTS]
        







