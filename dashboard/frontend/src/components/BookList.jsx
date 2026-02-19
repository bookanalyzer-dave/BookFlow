import React, { useState, useMemo, useEffect } from 'react';
import { useBooks } from '../hooks/useBooks';
import { useAuth } from '../context/AuthContext';
import { db } from '../firebaseConfig';
import { doc, deleteDoc, onSnapshot } from 'firebase/firestore';
import toast from 'react-hot-toast';

// --- SUBCOMPONENTS (Extracted for readability) ---

const DataRow = ({ label, value }) => (
  <div className="flex justify-between py-2 border-b border-gray-100 last:border-0">
    <span className="text-gray-500 text-sm font-medium">{label}</span>
    <span className="text-gray-900 text-sm font-semibold text-right">{value || 'N/A'}</span>
  </div>
);

const StatusBadge = ({ status }) => {
  const config = {
    priced: { bg: "bg-emerald-100", text: "text-emerald-800", ring: "ring-emerald-600/20", label: "Bepreist" },
    needs_review: { bg: "bg-amber-100", text: "text-amber-800", ring: "ring-amber-600/20", label: "Prüfung" },
    ingesting: { bg: "bg-blue-100", text: "text-blue-800", ring: "ring-blue-600/20", label: "Analyse", animate: "animate-pulse" },
    analysis_failed: { bg: "bg-rose-100", text: "text-rose-800", ring: "ring-rose-600/20", label: "Fehler" },
    default: { bg: "bg-gray-100", text: "text-gray-800", ring: "ring-gray-600/20", label: status }
  };
  
  const style = config[status] || config.default;

  return (
    <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${style.bg} ${style.text} ${style.ring} ${style.animate || ''}`}>
      {style.label}
    </span>
  );
};

const BookDetailView = ({ book, onClose, onDelete }) => {
  const { currentUser } = useAuth();
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [detailedCondition, setDetailedCondition] = useState(null);

  // Effect for fetching detailed condition
  useEffect(() => {
    if (book && currentUser) {
      setCurrentImageIndex(0);
      setDetailedCondition(null);
      const assessmentRef = doc(db, 'users', currentUser.uid, 'condition_assessments', book.id);
      const unsubscribe = onSnapshot(assessmentRef, (docSnap) => {
        if (docSnap.exists()) setDetailedCondition(docSnap.data());
      });
      return () => unsubscribe();
    }
  }, [book, currentUser]);

  if (!book) return null;

  const imageUrl = (url) => 
    url?.startsWith('gs://') ? url.replace('gs://', 'https://storage.googleapis.com/') : url;

  return (
    <div className="bg-white shadow-2xl rounded-2xl overflow-hidden max-w-5xl mx-auto animate-fade-in-up border border-gray-100 my-8">
      {/* Header */}
      <div className="bg-white px-6 py-4 flex justify-between items-center border-b border-gray-100 sticky top-0 z-10 backdrop-blur-sm bg-white/90">
        <button
          onClick={onClose}
          className="group flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors font-medium text-sm"
        >
          <div className="p-1.5 rounded-full bg-gray-100 group-hover:bg-gray-200 transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          </div>
          Zurück zur Liste
        </button>
        <div className="flex gap-4 items-center">
          <StatusBadge status={book.status} />
          <button
            onClick={() => onDelete(book.id)}
            className="text-red-500 hover:text-red-700 text-xs font-bold uppercase tracking-wider transition-colors border border-red-200 hover:border-red-300 rounded-lg px-3 py-1.5 hover:bg-red-50"
          >
            Löschen
          </button>
        </div>
      </div>

      <div className="p-6 lg:p-10 grid grid-cols-1 md:grid-cols-12 gap-10">
        {/* LEFT COLUMN: VISUALS */}
        <div className="md:col-span-5 flex flex-col gap-6">
          <div className="relative aspect-[3/4] bg-gray-50 rounded-2xl overflow-hidden shadow-sm border border-gray-100 group">
            {book.imageUrls?.length > 0 ? (
              <>
                <div className="absolute inset-0 flex items-center justify-center p-4">
                  <img
                    src={imageUrl(book.imageUrls[currentImageIndex])}
                    alt="Buchansicht"
                    className="max-h-full max-w-full object-contain drop-shadow-md transition-transform duration-300"
                  />
                </div>
                {book.imageUrls.length > 1 && (
                  <>
                    <button
                      onClick={(e) => { e.stopPropagation(); setCurrentImageIndex(p => p > 0 ? p - 1 : book.imageUrls.length - 1); }}
                      className="absolute left-3 top-1/2 -translate-y-1/2 p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-lg hover:bg-white text-gray-700 opacity-0 group-hover:opacity-100 transition-all transform hover:scale-110"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); setCurrentImageIndex(p => p < book.imageUrls.length - 1 ? p + 1 : 0); }}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-lg hover:bg-white text-gray-700 opacity-0 group-hover:opacity-100 transition-all transform hover:scale-110"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                    </button>
                    <div className="absolute inset-x-0 bottom-4 flex justify-center gap-2">
                      {book.imageUrls.map((_, i) => (
                        <div key={i} className={`h-1.5 rounded-full transition-all duration-300 shadow-sm ${i === currentImageIndex ? 'w-6 bg-white' : 'w-1.5 bg-white/50'}`} />
                      ))}
                    </div>
                  </>
                )}
              </>
            ) : (
               <div className="flex flex-col items-center justify-center h-full text-gray-300">
                 <svg className="w-16 h-16 opacity-20 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                 <span className="text-sm font-medium opacity-40">Kein Bild</span>
               </div>
            )}
          </div>
          
          {book.imageUrls?.length > 1 && (
            <div className="flex gap-3 overflow-x-auto pb-2 px-1 justify-center">
              {book.imageUrls.map((url, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentImageIndex(i)}
                  className={`relative flex-shrink-0 h-16 w-12 rounded-lg overflow-hidden transition-all duration-200 ${i === currentImageIndex ? 'ring-2 ring-blue-500 ring-offset-2' : 'opacity-60 hover:opacity-100'}`}
                >
                  <img
                    src={imageUrl(url)}
                    className="w-full h-full object-cover"
                    alt={`Thumb ${i + 1}`}
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: DATA */}
        <div className="md:col-span-7 space-y-8">
          <div>
            <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 leading-tight tracking-tight">
              {book.title || "Unbenanntes Buch"}
            </h1>
            <p className="text-lg text-gray-500 mt-2 font-medium">
              {Array.isArray(book.authors) ? book.authors.join(', ') : (book.author || "Unbekannter Autor")}
            </p>
          </div>

          {/* Pricing Card */}
          {book.calculatedPrice && (
            <div className="bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100 rounded-2xl p-6 shadow-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-emerald-100 rounded-full opacity-50 blur-xl"></div>
              
              <div className="relative z-10">
                <div className="flex justify-between items-end mb-4">
                  <div>
                    <span className="block text-emerald-700 font-bold text-xs uppercase tracking-widest mb-1">Geschätzter Marktwert</span>
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-black text-emerald-900 tracking-tight">€{book.calculatedPrice.toFixed(2)}</span>
                    </div>
                  </div>
                  {/* Confidence Badge */}
                  {book.price_analysis?.confidence && (
                    <div className="text-right">
                       <div className="inline-flex items-center px-2.5 py-1 rounded-lg bg-white/60 border border-emerald-100 shadow-sm backdrop-blur-sm">
                         <span className="text-xs font-bold text-emerald-800">
                           {(book.price_analysis.confidence * 100).toFixed(0)}% Konfidenz
                         </span>
                       </div>
                    </div>
                  )}
                </div>

                {/* Strategy & Stats */}
                {book.price_analysis && (
                   <div className="flex gap-2 mb-4 flex-wrap">
                     <span className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide border ${
                        book.price_analysis.strategy_used === 'aggressive' ? 'bg-rose-100 text-rose-800 border-rose-200' :
                        book.price_analysis.strategy_used === 'patient' ? 'bg-blue-100 text-blue-800 border-blue-200' :
                        'bg-white/50 text-emerald-800 border-emerald-200'
                     }`}>
                       Strategy: {book.price_analysis.strategy_used || 'Standard'}
                     </span>
                     <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-white/50 text-emerald-800 border border-emerald-200">
                       {book.price_analysis.competitor_count || 0} Konkurrenten
                     </span>
                   </div>
                )}

                {/* Price Range Visual */}
                {book.price_analysis?.market_price_range && (
                  <div className="mb-4 bg-white/40 rounded-lg p-3 border border-emerald-100/50">
                    <div className="flex justify-between text-[10px] font-bold text-emerald-700 uppercase tracking-wide mb-1.5">
                      <span>Min</span>
                      <span>Avg</span>
                      <span>Max</span>
                    </div>
                    <div className="relative h-2 bg-emerald-200/30 rounded-full mb-1">
                       {/* This is a simplified visual representation */}
                       <div className="absolute top-0 bottom-0 left-[20%] right-[20%] bg-emerald-300/50 rounded-full"></div>
                       <div className="absolute top-0 bottom-0 left-[50%] w-1 bg-emerald-500 rounded-full -ml-0.5"></div>
                    </div>
                    <div className="flex justify-between text-xs font-medium text-emerald-900">
                      <span>€{book.price_analysis.market_price_range.min_price.toFixed(2)}</span>
                      <span>€{book.price_analysis.market_price_range.avg_price.toFixed(2)}</span>
                      <span>€{book.price_analysis.market_price_range.max_price.toFixed(2)}</span>
                    </div>
                  </div>
                )}

                {/* Reasoning */}
                {(book.price_analysis?.reasoning || book.pricing?.reasoning) && (
                  <p className="text-sm text-emerald-900/80 italic leading-relaxed bg-white/40 p-3 rounded-lg border border-emerald-100/50">
                    "{book.price_analysis?.reasoning || book.pricing?.reasoning}"
                  </p>
                )}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Metadata */}
            <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100">
              <h4 className="text-gray-900 font-bold text-sm uppercase tracking-wider mb-5 flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                Details
              </h4>
              <div className="space-y-3">
                <DataRow label="ISBN" value={book.isbn} />
                <DataRow label="Verlag" value={book.publisher} />
                <DataRow label="Jahr" value={book.publication_year} />
                <DataRow label="Einband" value={book.binding_type} />
                <DataRow label="Gewicht" value={book.weight_grams ? `${book.weight_grams}g` : null} />
                <DataRow label="Sprache" value={book.language?.toUpperCase()} />
                <DataRow label="Seiten" value={book.page_count} />
                <DataRow label="Edition" value={book.edition} />
              </div>
            </div>

            {/* Condition */}
            {(book.ai_condition_grade || detailedCondition) && (
              <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm h-full">
                <h4 className="text-gray-900 font-bold text-sm uppercase tracking-wider mb-5 flex items-center gap-2">
                  <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  Zustand
                </h4>
                
                <div className="flex items-center gap-5 mb-6">
                  <div className="flex-shrink-0 w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center border-4 border-blue-100">
                    <span className="text-xl font-black text-blue-600">
                      {detailedCondition?.grade || book.ai_condition_grade || '?'}
                    </span>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 font-bold uppercase tracking-wide mb-1">KI-Score</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {detailedCondition?.overall_score?.toFixed(0) || book.ai_condition_score?.toFixed(0) || 0}%
                    </div>
                  </div>
                </div>

                {detailedCondition?.details?.summary && (
                  <p className="text-sm text-gray-600 mb-5 leading-relaxed bg-gray-50 p-3 rounded-lg">
                    {detailedCondition.details.summary}
                  </p>
                )}
                
                {detailedCondition?.details?.defects_list?.length > 0 && (
                  <div>
                    <span className="text-xs font-semibold text-gray-400 uppercase mb-2 block">Mängel</span>
                    <div className="flex flex-wrap gap-2">
                      {detailedCondition.details.defects_list.map((d, i) => (
                        <span key={i} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-red-50 text-red-700 border border-red-100">
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// --- MAIN COMPONENT ---

const BookList = () => {
  const { books, loading, error } = useBooks(); 
  const { currentUser } = useAuth();
  const [selectedBookId, setSelectedBookId] = useState(null);
  const [filter, setFilter] = useState('all');

  const selectedBook = useMemo(() => 
    books.find(b => b.id === selectedBookId) || null
  , [books, selectedBookId]);

  const handleDelete = async (bookId) => {
    if (!window.confirm('Dieses Buch wirklich löschen?')) return;
    const loadingToast = toast.loading('Lösche Buch...');
    try {
        await deleteDoc(doc(db, `users/${currentUser.uid}/books`, bookId));
        setSelectedBookId(null);
        toast.dismiss(loadingToast);
        toast.success('Buch erfolgreich gelöscht.');
    } catch (err) {
        console.error("Delete error:", err);
        toast.dismiss(loadingToast);
        toast.error('Fehler beim Löschen des Buches.');
    }
  };

  const filteredBooks = useMemo(() => {
    switch (filter) {
      case 'needs_review': return books.filter(b => b.status === 'needs_review');
      case 'priced': return books.filter(b => b.status === 'priced');
      default: return books;
    }
  }, [books, filter]);

  if (loading) return <div className="flex justify-center items-center h-64 text-gray-400 animate-pulse">Lade Inventar...</div>;
  if (error) return <div className="text-center py-10 text-red-600 bg-red-50 rounded-lg mx-auto max-w-2xl mt-10 p-6 border border-red-100">{error}</div>;

  // Detail View Mode
  if (selectedBook) {
    return (
      <BookDetailView 
        book={selectedBook} 
        onClose={() => setSelectedBookId(null)} 
        onDelete={handleDelete} 
      />
    );
  }

  // List View Mode
  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Header & Filter */}
      <div className="flex flex-col md:flex-row justify-between items-end md:items-center gap-6 border-b border-gray-100 pb-6">
        <div>
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">Bibliothek</h2>
          <p className="text-gray-500 mt-1 text-sm font-medium">Verwalte deine Buchsammlung effizient.</p>
        </div>
        
        <div className="flex items-center gap-4 w-full md:w-auto">
          <span className="hidden md:inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-700/10">
            {filteredBooks.length} Bücher
          </span>
          <div className="flex bg-gray-100/80 p-1 rounded-xl shadow-inner w-full md:w-auto">
            {[
              { id: 'all', label: 'Alle' },
              { id: 'priced', label: 'Gepreist' },
              { id: 'needs_review', label: 'Review' }
            ].map(f => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                className={`flex-1 md:flex-none px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ease-out ${
                  filter === f.id 
                    ? 'bg-white text-gray-900 shadow-sm ring-1 ring-gray-900/5' 
                    : 'text-gray-500 hover:text-gray-900 hover:bg-gray-200/50'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Grid */}
      {filteredBooks.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
          {filteredBooks.map((book) => (
            <div
              key={book.id}
              onClick={() => setSelectedBookId(book.id)}
              className="group bg-white rounded-2xl shadow-sm hover:shadow-xl hover:shadow-gray-200/50 transition-all duration-300 border border-gray-100 cursor-pointer overflow-hidden flex flex-col h-full hover:-translate-y-1 ring-1 ring-transparent hover:ring-gray-900/5"
            >
              <div className="aspect-[2/3] bg-gray-50 overflow-hidden relative">
                {book.imageUrls?.[0] ? (
                  <img
                    src={book.imageUrls[0].startsWith('gs://') ? book.imageUrls[0].replace('gs://', 'https://storage.googleapis.com/') : book.imageUrls[0]}
                    alt={book.title}
                    loading="lazy"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out"
                  />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-gray-300 bg-gray-50/50">
                    <span className="text-4xl opacity-20 mb-2">📚</span>
                    <span className="text-xs font-medium opacity-40">Kein Cover</span>
                  </div>
                )}
                {/* Status Overlay */}
                <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-all duration-300 transform scale-90 group-hover:scale-100 origin-top-right">
                   <StatusBadge status={book.status} />
                </div>
                {/* Gradient Overlay on Hover */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
              </div>
              
              <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                <div>
                  <h3 className="font-bold text-gray-900 text-sm line-clamp-2 leading-snug group-hover:text-blue-600 transition-colors" title={book.title}>
                    {book.title || "Unbenannt"}
                  </h3>
                  <p className="text-xs text-gray-500 truncate mt-1 font-medium">
                    {Array.isArray(book.authors) ? book.authors[0] : (book.author || "Unbekannter Autor")}
                  </p>
                </div>
                
                <div className="pt-3 flex justify-between items-center border-t border-gray-50">
                  <span className={`text-sm font-black tracking-tight ${book.calculatedPrice ? 'text-gray-900' : 'text-gray-300'}`}>
                    {book.calculatedPrice ? `€${book.calculatedPrice.toFixed(2)}` : "—"}
                  </span>
                  <div className={`h-2 w-2 rounded-full ring-2 ring-white shadow-sm ${
                    book.status === 'priced' ? 'bg-green-500' :
                    book.status === 'needs_review' ? 'bg-amber-400' :
                    'bg-gray-200'
                  }`} />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-24 bg-white rounded-3xl border border-dashed border-gray-200 shadow-sm text-center">
          <div className="h-20 w-20 bg-blue-50 rounded-full flex items-center justify-center mb-6">
            <svg className="w-10 h-10 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-2">Deine Bibliothek ist leer</h3>
          <p className="text-gray-500 max-w-sm mx-auto mb-8 text-sm leading-relaxed">
            Es sieht so aus, als hättest du noch keine Bücher hinzugefügt oder deine Filter sind zu strikt.
          </p>
          <div className="flex gap-4">
            <button 
              onClick={() => setFilter('all')} 
              className="px-6 py-2.5 text-sm font-semibold text-gray-700 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 focus:ring-4 focus:ring-gray-100 transition-all"
            >
              Filter löschen
            </button>
            <a 
              href="/upload" 
              className="px-6 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700 shadow-lg shadow-blue-600/20 focus:ring-4 focus:ring-blue-600/30 transition-all"
            >
              Neues Buch scannen
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default BookList;