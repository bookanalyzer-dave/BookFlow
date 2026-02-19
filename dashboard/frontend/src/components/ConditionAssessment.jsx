import React, { useState, useEffect } from 'react';
import { useConditionAssessment } from '../hooks/useConditionAssessment';
import { useAuth } from '../context/AuthContext';
import { doc, onSnapshot } from 'firebase/firestore'; // Still need onSnapshot for realtime updates during assessment flow?
// Actually, the hook handles the snapshot. But the component logic updates status based on the data.

const ConditionAssessment = ({ bookId, onAssessmentComplete }) => {
  const { assessment: hookAssessment, loading: hookLoading } = useConditionAssessment(bookId);
  const { currentUser } = useAuth();
  
  const [images, setImages] = useState([]);
  const [assessment, setAssessment] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, uploading, assessing, complete, error
  const [error, setError] = useState(null);
  const [manualOverride, setManualOverride] = useState(false);
  const [overrideGrade, setOverrideGrade] = useState('');
  const [overrideReason, setOverrideReason] = useState('');

  const conditionGrades = [
    { value: 'Fine', label: 'Fine (90-100%)', description: 'Wie neu, minimale Gebrauchsspuren' },
    { value: 'Very Fine', label: 'Very Fine (80-89%)', description: 'Leichte Abnutzung, strukturell einwandfrei' },
    { value: 'Good', label: 'Good (60-79%)', description: 'Moderate Gebrauchsspuren, vollständig' },
    { value: 'Fair', label: 'Fair (40-59%)', description: 'Deutliche Abnutzung, kleinere Mängel' },
    { value: 'Poor', label: 'Poor (0-39%)', description: 'Erhebliche Schäden, aber noch lesbar' }
  ];

  const imageTypes = [
    { value: 'cover', label: 'Buchcover', description: 'Vorderseite' },
    { value: 'spine', label: 'Buchrücken', description: 'Seitliche Ansicht' },
    { value: 'pages', label: 'Buchseiten', description: 'Innenseiten' },
    { value: 'binding', label: 'Bindung', description: 'Bindungsbereich' }
  ];

  // Sync hook data to local state
  useEffect(() => {
    if (hookAssessment) {
      setAssessment(hookAssessment);
      if (hookAssessment.status === 'pending') {
        setStatus('assessing');
      } else if (hookAssessment.grade) {
        setStatus('complete');
      }
    }
  }, [hookAssessment]);

  const handleImageChange = (e, imageType) => {
    const file = e.target.files[0];
    if (file) {
      setImages(prev => {
        const updated = prev.filter(img => img.type !== imageType);
        return [...updated, { file, type: imageType }];
      });
    }
  };

  const handleAssessment = async () => {
    if (images.length === 0) {
      setError('Bitte laden Sie mindestens ein Bild hoch');
      return;
    }

    setStatus('uploading');
    setError(null);

    try {
      const token = await currentUser.getIdToken();
      
      // Convert images to base64 for assessment
      const imageData = await Promise.all(
        images.map(async (img) => {
          const base64 = await fileToBase64(img.file);
          return {
            type: img.type,
            content: base64.split(',')[1] // Remove data:image/jpeg;base64, prefix
          };
        })
      );

      setStatus('assessing');

      // Call condition assessment API
      const response = await fetch(`${import.meta.env.VITE_BACKEND_API_URL}/api/books/assess-condition`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          bookId,
          images: imageData,
          metadata: {
            timestamp: new Date().toISOString()
          }
        }),
      });

      if (!response.ok) {
        throw new Error('Condition assessment failed');
      }

      const result = await response.json();
      setAssessment(result.condition_assessment);
      setStatus('complete');
      
      if (onAssessmentComplete) {
        onAssessmentComplete(result.condition_assessment);
      }

    } catch (err) {
      console.error('Assessment error:', err);
      setError(err.message);
      setStatus('error');
    }
  };

  const handleManualOverride = async () => {
    if (!overrideGrade || !overrideReason) {
      setError('Bitte geben Sie eine Bewertung und Begründung ein');
      return;
    }

    try {
      const token = await currentUser.getIdToken();
      
      const response = await fetch(`${import.meta.env.VITE_BACKEND_API_URL}/api/books/override-condition`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          bookId,
          overrideGrade,
          reason: overrideReason,
          timestamp: new Date().toISOString()
        }),
      });

      if (!response.ok) {
        throw new Error('Override failed');
      }

      const result = await response.json();
      setAssessment(prev => ({
        ...prev,
        grade: overrideGrade,
        manual_override: true,
        override_reason: overrideReason
      }));
      setManualOverride(false);
      
      if (onAssessmentComplete) {
        onAssessmentComplete(result.condition_assessment);
      }

    } catch (err) {
      console.error('Override error:', err);
      setError(err.message);
    }
  };

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  const getGradeColor = (grade) => {
    const colors = {
      'Fine': 'text-green-700 bg-green-50 border-green-200',
      'Very Fine': 'text-emerald-700 bg-emerald-50 border-emerald-200',
      'Good': 'text-yellow-700 bg-yellow-50 border-yellow-200',
      'Fair': 'text-orange-700 bg-orange-50 border-orange-200',
      'Poor': 'text-red-700 bg-red-50 border-red-200'
    };
    return colors[grade] || 'text-gray-700 bg-gray-50 border-gray-200';
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (hookLoading && !assessment) {
      return (
        <div className="p-12 flex flex-col items-center justify-center text-gray-400">
           <svg className="animate-spin h-8 w-8 text-blue-500 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
           <p className="text-sm font-medium">Lade Bewertung...</p>
        </div>
      );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 sm:p-8 bg-white rounded-2xl shadow-xl shadow-gray-200/50 border border-gray-100 my-8">
      <h2 className="text-2xl font-extrabold text-gray-900 mb-6 tracking-tight">
        Zustandsbewertung
      </h2>

      {/* Image Upload Section */}
      <div className="mb-10">
        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
           <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-600 text-xs font-bold">1</span>
           Bilder hochladen
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {imageTypes.map((type) => (
            <div key={type.value} className={`relative group border-2 border-dashed rounded-xl p-4 transition-all duration-200 ${images.find(img => img.type === type.value) ? 'border-green-300 bg-green-50/30' : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/30'}`}>
              <div className="text-center">
                <h4 className="font-semibold text-gray-900 mb-1">{type.label}</h4>
                <p className="text-xs text-gray-500 mb-4">{type.description}</p>
                
                <input
                  type="file"
                  accept="image/*"
                  id={`file-${type.value}`}
                  onChange={(e) => handleImageChange(e, type.value)}
                  className="hidden"
                />
                
                {images.find(img => img.type === type.value) ? (
                  <div className="flex items-center justify-center gap-2 text-green-700 bg-green-100 px-3 py-1.5 rounded-lg text-sm font-medium mx-auto w-fit">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                    Bereit
                    <label htmlFor={`file-${type.value}`} className="absolute inset-0 cursor-pointer" title="Ändern"></label>
                  </div>
                ) : (
                  <label 
                    htmlFor={`file-${type.value}`}
                    className="cursor-pointer inline-flex items-center gap-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 px-4 py-2 rounded-lg transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                    Auswählen
                  </label>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Assessment Button */}
      {!assessment && (
        <div className="mb-8">
          <button
            onClick={handleAssessment}
            disabled={images.length === 0 || status === 'uploading' || status === 'assessing'}
            className={`w-full py-4 px-6 rounded-xl text-white font-bold text-lg shadow-lg transition-all transform duration-200 focus:outline-none focus:ring-4 focus:ring-offset-2 ${
              images.length === 0 || status === 'uploading' || status === 'assessing'
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed shadow-none'
              : 'bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 hover:-translate-y-0.5 shadow-blue-500/30 focus:ring-blue-500'
            }`}
          >
            {status === 'uploading' && 'Bilder werden verarbeitet...'}
            {status === 'assessing' && 'KI analysiert Zustand...'}
            {status === 'idle' && `Jetzt bewerten (${images.length} Bilder)`}
          </button>
        </div>
      )}

      {/* Assessment Results */}
      {assessment && (
        <div className="animate-fade-in-up">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-green-100 text-green-600 text-xs font-bold">2</span>
            Ergebnis
          </h3>
          
          {/* Overall Grade */}
          <div className="bg-gray-50 rounded-2xl p-6 mb-6 border border-gray-100">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                 <div className="flex flex-col items-center">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Grade</span>
                    <span className={`inline-block px-4 py-1.5 rounded-lg text-sm font-bold border shadow-sm ${getGradeColor(assessment.grade)}`}>
                      {assessment.grade}
                    </span>
                 </div>
                 <div className="h-10 w-px bg-gray-200"></div>
                 <div className="flex flex-col items-center">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Score</span>
                    <span className="text-2xl font-black text-gray-900">{assessment.overall_score?.toFixed(0)}%</span>
                 </div>
              </div>
              
              <div className="text-right">
                <span className="text-xs font-medium text-gray-500 block mb-1">KI-Konfidenz</span>
                <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-gray-200 shadow-sm ${getConfidenceColor(assessment.confidence)}`}>
                   <div className={`w-2 h-2 rounded-full ${assessment.confidence >= 0.8 ? 'bg-green-500' : assessment.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
                   <span className="font-bold text-sm">{(assessment.confidence * 100)?.toFixed(0)}%</span>
                </div>
              </div>
            </div>

            {assessment.manual_override && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mt-6 flex gap-3">
                <svg className="w-5 h-5 text-amber-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                <div>
                   <p className="text-amber-900 font-bold text-sm">Manuell korrigiert</p>
                   <p className="text-amber-800 text-sm mt-1">{assessment.override_reason}</p>
                </div>
              </div>
            )}
          </div>

          {/* Component Scores */}
          {assessment.component_scores && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
              {Object.entries(assessment.component_scores).map(([component, score]) => (
                <div key={component} className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-semibold text-gray-700 capitalize text-sm">
                      {imageTypes.find(type => type.value === component)?.label || component}
                    </h4>
                    <span className="text-sm font-bold text-gray-900">{score?.toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div className="bg-blue-500 h-2 rounded-full transition-all duration-500" style={{ width: `${score}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Detailed Analysis */}
          {assessment.details && (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden mb-6">
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <h4 className="font-bold text-gray-900 text-sm">KI-Detailanalyse</h4>
              </div>
              <div className="p-4 space-y-3">
                {Object.entries(assessment.details).map(([key, value]) => (
                  <div key={key} className="flex flex-col sm:flex-row sm:justify-between text-sm gap-1 sm:gap-4 border-b border-gray-50 last:border-0 pb-2 last:pb-0">
                    <span className="text-gray-500 capitalize font-medium whitespace-nowrap">
                      {key.replace(/_/g, ' ')}
                    </span>
                    <span className="text-gray-900 font-medium text-right">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Manual Override Section */}
          <div className="border-t border-gray-100 pt-6">
            {!manualOverride ? (
              <button
                onClick={() => setManualOverride(true)}
                className="text-gray-500 hover:text-gray-900 text-sm font-medium flex items-center gap-2 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                Ergebnis korrigieren
              </button>
            ) : (
              <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                <h4 className="font-bold text-gray-900 mb-4">Manuelle Korrektur</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2">
                      Neue Bewertung
                    </label>
                    <div className="relative">
                      <select
                        value={overrideGrade}
                        onChange={(e) => setOverrideGrade(e.target.value)}
                        className="block w-full pl-3 pr-10 py-3 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-lg shadow-sm"
                      >
                        <option value="">Bitte wählen...</option>
                        {conditionGrades.map((grade) => (
                          <option key={grade.value} value={grade.value}>
                            {grade.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2">
                      Begründung
                    </label>
                    <textarea
                      value={overrideReason}
                      onChange={(e) => setOverrideReason(e.target.value)}
                      placeholder="Warum weicht Ihre Einschätzung ab?"
                      className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-lg p-3 min-h-[100px]"
                    />
                  </div>
                  <div className="flex gap-3 pt-2">
                    <button
                      onClick={handleManualOverride}
                      className="bg-gray-900 text-white px-5 py-2.5 rounded-lg text-sm font-bold hover:bg-black transition-colors shadow-sm"
                    >
                      Korrektur speichern
                    </button>
                    <button
                      onClick={() => setManualOverride(false)}
                      className="bg-white text-gray-700 border border-gray-300 px-5 py-2.5 rounded-lg text-sm font-bold hover:bg-gray-50 transition-colors"
                    >
                      Abbrechen
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 flex gap-3 text-red-800">
           <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
           <p className="font-medium">{error}</p>
        </div>
      )}

      {/* Status Display */}
      {status === 'assessing' && (
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 flex gap-3 text-blue-800 animate-pulse">
          <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          <p className="font-bold">
            KI-basierte Zustandsbewertung wird durchgeführt...
          </p>
        </div>
      )}
    </div>
  );
};

export default ConditionAssessment;