import React, { useState, useEffect } from 'react';
import { db } from '../firebaseConfig';
import { doc, onSnapshot } from 'firebase/firestore';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';

const ImageUpload = () => {
  const { currentUser } = useAuth();
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState('idle'); // idle, uploading, processing, success, error
  const [progress, setProgress] = useState(0);
  const [processingBookId, setProcessingBookId] = useState(null);

  useEffect(() => {
    let unsubscribe;

    if (processingBookId && currentUser) {
      console.log(`Waiting for analysis results for book: ${processingBookId}`);
      const bookRef = doc(db, 'users', currentUser.uid, 'books', processingBookId);

      unsubscribe = onSnapshot(bookRef, (docSnap) => {
        if (docSnap.exists()) {
          const data = docSnap.data();
          console.log("Firestore update received:", data.status);

          if (['pending_analysis', 'ingesting'].includes(data.status)) {
            setStatus('processing');
            setProgress(50);
          }
          else if (data.status === 'ingested' && data.title && data.authors) {
            toast.success(`Buch "${data.title}" erfolgreich analysiert!`);
            setStatus('success');
            setProgress(100);
            setProcessingBookId(null);
          }
          else if (['analysis_failed', 'failed'].includes(data.status)) {
            const errMsg = data.error || 'Unbekannter Fehler';
            toast.error(`Analyse fehlgeschlagen: ${errMsg}`);
            setStatus('error');
            setProcessingBookId(null);
          }
        }
      }, (err) => {
        console.error("Firestore listener error:", err);
        toast.error("Fehler beim Abrufen der Ergebnisse");
        setStatus('error');
        setProcessingBookId(null);
      });
    }

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, [processingBookId, currentUser]);

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
      setStatus('idle');
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    if (!currentUser) {
        toast.error("Bitte melden Sie sich an.");
        return;
    }

    setStatus('uploading');
    setProgress(0);

    const loadingToast = toast.loading('Starte Upload...');

    try {
      const token = await currentUser.getIdToken();
      const totalFiles = files.length;
      let completedFiles = 0;

      // 1. Get signed URLs for all files
      const uploadPromises = files.map(async (file) => {
        const contentType = file.type || 'application/octet-stream';

        const response = await fetch(`${import.meta.env.VITE_BACKEND_API_URL}/api/books/upload`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ filename: file.name, contentType }),
        });

        if (!response.ok) {
          throw new Error(`Signatur-Fehler: ${response.status}`);
        }

        const data = await response.json();
        const { url, gcs_uri } = data;

        // 2. Upload file to GCS
        const uploadResponse = await fetch(url, {
          method: 'PUT',
          headers: { 'Content-Type': contentType },
          body: file,
        });

        if (!uploadResponse.ok) {
          throw new Error(`Upload fehlgeschlagen: ${uploadResponse.status}`);
        }
        
        completedFiles++;
        setProgress(Math.round((completedFiles / totalFiles) * 50));
        return gcs_uri;
      });

      const gcsUris = await Promise.all(uploadPromises);
      
      toast.dismiss(loadingToast);
      toast.success('Bilder hochgeladen, starte Analyse...', { duration: 3000 });
      
      setStatus('processing');
      setProgress(60);

      // 3. Start processing
      const processResponse = await fetch(`${import.meta.env.VITE_BACKEND_API_URL}/api/books/start-processing`, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ gcs_uris: gcsUris }),
      });
      
      if (!processResponse.ok) {
          throw new Error('Verarbeitung konnte nicht gestartet werden.');
      }

      const processResult = await processResponse.json();

      if (processResult.bookId) {
        setProcessingBookId(processResult.bookId);
      } else {
        throw new Error("Keine Book-ID vom Server erhalten.");
      }
      
      setFiles([]); 

    } catch (err) {
      console.error(err);
      toast.dismiss(loadingToast);
      toast.error(err.message || "Ein unerwarteter Fehler ist aufgetreten.");
      setStatus('error');
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4 sm:p-6 bg-white border border-gray-200 rounded-xl shadow-sm my-4 sm:my-8">
      <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6">Bilder hochladen & Analysieren</h2>
      
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Bilder auswählen</label>
        <div className="flex items-center justify-center w-full">
          <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-48 sm:h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <svg className="w-10 h-10 mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
              <p className="mb-2 text-sm text-gray-500"><span className="font-semibold">Klicken zum Hochladen</span> oder Drag & Drop</p>
              <p className="text-xs text-gray-500">Bilder von Cover, Rückseite und Impressum (PNG, JPG)</p>
            </div>
            <input 
              id="dropzone-file" 
              type="file" 
              className="hidden" 
              onChange={handleFileChange} 
              multiple 
              accept="image/*"
            />
          </label>
        </div>
        
        {files.length > 0 && (
          <div className="mt-4">
             <p className="text-sm text-gray-600 font-medium">Ausgewählte Dateien ({files.length}):</p>
             <ul className="mt-2 space-y-1">
               {files.map((file, index) => (
                 <li key={index} className="text-xs text-gray-500 flex items-center">
                   <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                   {file.name}
                 </li>
               ))}
             </ul>
          </div>
        )}
      </div>

      <button 
        onClick={handleUpload} 
        disabled={files.length === 0 || status === 'uploading' || status === 'processing'}
        className={`w-full py-3 px-4 rounded-lg text-white font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
            files.length === 0 || status === 'uploading' || status === 'processing'
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 shadow-md'
        }`}
      >
        {status === 'uploading' ? 'Lade hoch...' : status === 'processing' ? 'Analysiere...' : `Upload & Analyse starten`}
      </button>

      {(status === 'uploading' || status === 'processing') && (
        <div className="mt-6 space-y-2">
          <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
            <div 
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-500 ease-in-out" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-sm text-center text-gray-600 animate-pulse">
            {status === 'uploading' ? 'Bilder werden hochgeladen...' : 'KI analysiert Buchdaten...'}
          </p>
        </div>
      )}
    </div>
  );
};

export default ImageUpload;