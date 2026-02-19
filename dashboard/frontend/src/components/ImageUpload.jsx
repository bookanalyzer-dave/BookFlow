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
    <div className="w-full max-w-2xl mx-auto p-4 sm:p-8 bg-white border border-gray-100 rounded-2xl shadow-xl shadow-gray-200/50 my-8 sm:my-12">
      <div className="text-center mb-8">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">Neues Buch scannen</h2>
        <p className="mt-2 text-gray-500">Lade Fotos von Cover, Rückseite und Impressum hoch.</p>
      </div>
      
      <div className="mb-8">
        <div className="flex items-center justify-center w-full group">
          <label htmlFor="dropzone-file" className={`flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-300 ${files.length > 0 ? 'border-blue-300 bg-blue-50/30' : 'border-gray-300 bg-gray-50 hover:bg-gray-100 hover:border-gray-400'}`}>
            <div className="flex flex-col items-center justify-center pt-5 pb-6 text-center px-4">
              <div className={`p-4 rounded-full mb-3 transition-colors ${files.length > 0 ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400 group-hover:bg-gray-200 group-hover:text-gray-500'}`}>
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
              </div>
              <p className="mb-2 text-sm text-gray-900 font-medium">
                <span className="text-blue-600 hover:underline">Klicken zum Auswählen</span> oder hierher ziehen
              </p>
              <p className="text-xs text-gray-500 max-w-xs leading-relaxed">Unterstützt: JPG, PNG (Max. 10MB pro Datei)</p>
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
          <div className="mt-6 bg-gray-50 rounded-xl p-4 border border-gray-100">
             <div className="flex justify-between items-center mb-3">
               <span className="text-xs font-bold uppercase tracking-wider text-gray-500">Ausgewählt ({files.length})</span>
               <button onClick={() => setFiles([])} className="text-xs text-red-500 hover:text-red-700 font-medium">Alle entfernen</button>
             </div>
             <ul className="space-y-2">
               {files.map((file, index) => (
                 <li key={index} className="flex items-center justify-between bg-white p-2 rounded-lg border border-gray-100 shadow-sm">
                   <div className="flex items-center min-w-0">
                     <span className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-500 rounded-md flex items-center justify-center mr-3">
                       <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                     </span>
                     <span className="text-sm text-gray-700 truncate font-medium">{file.name}</span>
                   </div>
                   <span className="text-xs text-gray-400 ml-2 whitespace-nowrap">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                 </li>
               ))}
             </ul>
          </div>
        )}
      </div>

      <button 
        onClick={handleUpload} 
        disabled={files.length === 0 || status === 'uploading' || status === 'processing'}
        className={`w-full py-4 px-6 rounded-xl text-white font-bold text-lg shadow-lg transition-all transform duration-200 focus:outline-none focus:ring-4 focus:ring-offset-2 ${
            files.length === 0 || status === 'uploading' || status === 'processing'
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed shadow-none'
            : 'bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 hover:-translate-y-0.5 shadow-blue-500/30 focus:ring-blue-500'
        }`}
      >
        {status === 'uploading' ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            Lade hoch...
          </span>
        ) : status === 'processing' ? (
           <span className="flex items-center justify-center gap-2">
             <span className="relative flex h-3 w-3"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span><span className="relative inline-flex rounded-full h-3 w-3 bg-white"></span></span>
             Analysiere...
           </span>
        ) : `Upload & Analyse starten`}
      </button>

      {(status === 'uploading' || status === 'processing') && (
        <div className="mt-8 space-y-3">
          <div className="flex justify-between text-xs font-semibold text-gray-500 uppercase tracking-wide">
            <span>Fortschritt</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden shadow-inner">
            <div 
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out shadow-sm" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-sm text-center text-gray-600 font-medium animate-pulse mt-2">
            {status === 'uploading' ? 'Bilder werden sicher übertragen...' : 'Künstliche Intelligenz analysiert dein Buch...'}
          </p>
        </div>
      )}
    </div>
  );
};

export default ImageUpload;