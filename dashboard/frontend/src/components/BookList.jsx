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
  const styles = {
    priced: "bg-green-100 text-green-800",
    needs_review: "bg-yellow-100 text-yellow-800",
    ingesting: "bg-blue-100 text-blue-800 animate-pulse",
    analysis_failed: "bg-red-100 text-red-800"
  };
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${styles[status] || "bg-gray-100 text-gray-800"}`}>
      {status}
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
    <div className="bg-white shadow-lg rounded-xl overflow-hidden max-w-4xl mx-auto animate-fade-in-up">
      <div className="bg-gray-50 px-4 py-3 flex justify-between items-center border-b border-gray-200">
        <button
          onClick={onClose}
          className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 text-sm transition-colors"
        >
          ← Zurück
        </button>
        <div className="flex gap-3 items-center">
          <StatusBadge status={book.status} />
          <button
            onClick={() => onDelete(book.id)}
            className="text-red-500 hover:text-red-700 text-xs font-medium transition-colors"
          >
            Löschen
          </button>
        </div>
      </div>

      <div className="p-6 grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* LEFT COLUMN: VISUALS (Smaller column span) */}
        <div className="md:col-span-5 space-y-4">
          <div className="relative aspect-[2/3] bg-gray-100 rounded-lg overflow-hidden shadow-inner flex items-center justify-center group">
            {book.imageUrls?.length > 0 ? (
              <>
                <img
                  src={imageUrl(book.imageUrls[currentImageIndex])}
                  alt="Buchansicht"
                  className="max-h-full max-w-full object-contain transition-transform duration-300"
                />
                {book.imageUrls.length > 1 && (
                  <>
                    <button
                      onClick={(e) => { e.stopPropagation(); setCurrentImageIndex(p => p > 0 ? p - 1 : book.imageUrls.length - 1); }}
                      className="absolute left-2 top-1/2 -translate-y-1/2 p-1.5 bg-white/90 rounded-full shadow hover:bg-white opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      ‹
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); setCurrentImageIndex(p => p < book.imageUrls.length - 1 ? p + 1 : 0); }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-white/90 rounded-full shadow hover:bg-white opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      ›
                    </button>
                    <div className="absolute inset-x-0 bottom-3 flex justify-center gap-1.5">
                      {book.imageUrls.map((_, i) => (
                        <div key={i} className={`h-1 w-1 rounded-full transition-colors ${i === currentImageIndex ? 'bg-blue-600' : 'bg-gray-300'}`} />
                      ))}
                    </div>
                  </>
                )}
              </>
            ) : <div className="text-gray-400 italic text-sm">Kein Bild</div>}
          </div>
          
          <div className="flex flex-wrap gap-2 justify-center">
            {book.imageUrls?.map((url, i) => (
              <button
                key={i}
                onClick={() => setCurrentImageIndex(i)}
                className={`h-12 w-9 rounded border overflow-hidden transition-all ${i === currentImageIndex ? 'border-blue-500 ring-1 ring-blue-100' : 'border-transparent hover:border-gray-300'}`}
              >
                <img
                  src={imageUrl(url)}
                  className="w-full h-full object-cover"
                  alt={`Thumbnail ${i + 1}`}
                />
              </button>
            ))}
          </div>
        </div>

        {/* RIGHT COLUMN: DATA (Larger column span) */}
        <div className="md:col-span-7 space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 leading-tight">
              {book.title || "Unbenanntes Buch"}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              von {Array.isArray(book.authors) ? book.authors.join(', ') : (book.author || "Unbekannter Autor")}
            </p>
          </div>

          {/* Price Section */}
          {book.calculatedPrice && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 shadow-sm">
              <div className="flex justify-between items-baseline">
                <span className="text-green-700 font-bold uppercase text-[10px] tracking-widest">Marktwert</span>
                <span className="text-2xl font-black text-green-900">€{book.calculatedPrice.toFixed(2)}</span>
              </div>
              {book.pricing?.reasoning && (
                <p className="mt-2 text-xs text-green-800 italic leading-relaxed">
                  "{book.pricing.reasoning}"
                </p>
              )}
              {book.pricing?.sources?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-green-200">
                  <h5 className="text-green-900 font-bold text-xs uppercase mb-2">Quellen:</h5>
                  <ul className="space-y-1">
                    {book.pricing.sources.map((source, idx) => {
                      const url = typeof source === 'string' ? source : source.url;
                      const label = typeof source === 'string' 
                        ? (url && url.length > 40 ? url.substring(0, 40) + '...' : url) 
                        : (source.title || url);
                      return (
                        <li key={idx} className="text-xs truncate">
                          <a href={url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                            {label}
                          </a>
                          {typeof source === 'object' && source.price && <span className="ml-1 text-gray-600">- €{source.price.toFixed(2)}</span>}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Core Metadata */}
          <div className="bg-gray-50 rounded-xl p-6 space-y-1 shadow-sm">
            <h4 className="text-gray-400 font-bold text-xs uppercase tracking-widest mb-4">Bibliografische Daten</h4>
            <DataRow label="ISBN" value={book.isbn} />
            <DataRow label="Verlag" value={book.publisher} />
            <DataRow label="Jahr" value={book.publication_year} />
            <DataRow label="Einband" value={book.binding_type} />
            <DataRow label="Gewicht" value={book.weight_grams ? `${book.weight_grams}g` : null} />
            <DataRow label="Sprache" value={book.language?.toUpperCase()} />
            <DataRow label="Seiten" value={book.page_count} />
            <DataRow label="Edition" value={book.edition} />
          </div>

          {/* Condition Section */}
          {(book.ai_condition_grade || detailedCondition) && (
            <div className="border border-gray-200 rounded-xl p-6 shadow-sm">
              <h4 className="text-gray-400 font-bold text-xs uppercase tracking-widest mb-4">Zustandsbewertung</h4>
              <div className="flex items-center gap-4 mb-4">
                <div className="text-2xl font-bold text-gray-900">{detailedCondition?.grade || book.ai_condition_grade}</div>
                <div className="h-4 w-px bg-gray-200" />
                <div className="text-gray-500">Score: <span className="text-gray-900 font-semibold">{detailedCondition?.overall_score?.toFixed(1) || book.ai_condition_score?.toFixed(1) || 'N/A'}%</span></div>
              </div>
              {detailedCondition?.details?.summary && (
                <p className="text-sm text-gray-600 mb-4 leading-relaxed">{detailedCondition.details.summary}</p>
              )}
              {detailedCondition?.details?.defects_list?.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {detailedCondition.details.defects_list.map((d, i) => (
                    <span key={i} className="bg-red-50 text-red-700 text-[10px] px-2 py-0.5 rounded border border-red-100">
                      {d}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
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
    <div className="space-y-8 animate-fade-in">
      {/* Header & Filter */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Bibliothek <span className="text-gray-400 font-normal text-lg ml-2">{filteredBooks.length} Bücher</span></h2>
        <div className="w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          <div className="flex bg-white p-1 rounded-lg shadow-sm border border-gray-200 min-w-max">
            {[
              { id: 'all', label: 'Alle' },
              { id: 'priced', label: 'Gepreist' },
              { id: 'needs_review', label: 'Review' }
            ].map(f => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-all whitespace-nowrap ${
                  filter === f.id ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
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
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {filteredBooks.map((book) => (
            <div
              key={book.id}
              onClick={() => setSelectedBookId(book.id)}
              className="group bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-200 border border-gray-100 cursor-pointer overflow-hidden flex flex-col h-full hover:-translate-y-0.5"
            >
              <div className="aspect-[2/3] bg-gray-50 overflow-hidden relative">
                {book.imageUrls?.[0] ? (
                  <img
                    src={book.imageUrls[0].startsWith('gs://') ? book.imageUrls[0].replace('gs://', 'https://storage.googleapis.com/') : book.imageUrls[0]}
                    alt={book.title}
                    loading="lazy"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-300 bg-gray-50">
                    <span className="text-2xl opacity-20">📖</span>
                  </div>
                )}
                {/* Status Overlay on Hover */}
                <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity scale-75 origin-top-right">
                   <StatusBadge status={book.status} />
                </div>
              </div>
              
              <div className="p-3 flex-1 flex flex-col justify-between space-y-1">
                <div>
                  <h3 className="font-semibold text-gray-900 text-xs line-clamp-2 leading-tight" title={book.title}>
                    {book.title || "Unbenannt"}
                  </h3>
                  <p className="text-[10px] text-gray-500 truncate mt-0.5">
                    {Array.isArray(book.authors) ? book.authors[0] : (book.author || "Unbekannter Autor")}
                  </p>
                </div>
                
                <div className="pt-1.5 flex justify-between items-center border-t border-gray-50 mt-1">
                  <span className={`text-xs font-bold ${book.calculatedPrice ? 'text-gray-900' : 'text-gray-300'}`}>
                    {book.calculatedPrice ? `€${book.calculatedPrice.toFixed(2)}` : "—"}
                  </span>
                  <div className={`h-1.5 w-1.5 rounded-full ring-1 ring-white ${
                    book.status === 'priced' ? 'bg-green-500' :
                    book.status === 'needs_review' ? 'bg-yellow-500' :
                    'bg-gray-300'
                  }`} />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200">
          <p className="text-gray-500 font-medium">Keine Bücher gefunden.</p>
          <button onClick={() => setFilter('all')} className="text-blue-600 text-sm mt-2 hover:underline">
            Filter zurücksetzen
          </button>
        </div>
      )}
    </div>
  );
};

export default BookList;