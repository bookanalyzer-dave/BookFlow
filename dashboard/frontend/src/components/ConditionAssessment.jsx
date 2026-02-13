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
    { value: 'cover', label: 'Buchcover', description: 'Vorderseite des Buchs' },
    { value: 'spine', label: 'Buchrücken', description: 'Seitliche Ansicht des Buchs' },
    { value: 'pages', label: 'Buchseiten', description: 'Innenseiten des Buchs' },
    { value: 'binding', label: 'Bindung', description: 'Bindungsbereich des Buchs' }
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
      // The hook will update the state via Firestore listener, but we can set it here too for immediate feedback
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
      'Fine': 'text-green-600 bg-green-50',
      'Very Fine': 'text-green-500 bg-green-50',
      'Good': 'text-yellow-600 bg-yellow-50',
      'Fair': 'text-orange-600 bg-orange-50',
      'Poor': 'text-red-600 bg-red-50'
    };
    return colors[grade] || 'text-gray-600 bg-gray-50';
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (hookLoading && !assessment) {
      return <div className="p-6 text-center text-gray-500">Lade Bewertung...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 bg-white rounded-lg shadow-lg my-4 sm:my-8">
      <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-4 sm:mb-6">
        Buchzustand-Bewertung
      </h2>

      {/* Image Upload Section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Bilder für Bewertung hochladen</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {imageTypes.map((type) => (
            <div key={type.value} className="border-2 border-dashed border-gray-300 rounded-lg p-4">
              <div className="text-center">
                <h4 className="font-medium text-gray-700">{type.label}</h4>
                <p className="text-sm text-gray-500 mb-3">{type.description}</p>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleImageChange(e, type.value)}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                {images.find(img => img.type === type.value) && (
                  <p className="text-green-600 text-sm mt-2">✓ Bild hochgeladen</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Assessment Button */}
      {!assessment && (
        <div className="mb-6">
          <button
            onClick={handleAssessment}
            disabled={images.length === 0 || status === 'uploading' || status === 'assessing'}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold disabled:bg-gray-400 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors"
          >
            {status === 'uploading' && 'Bilder werden verarbeitet...'}
            {status === 'assessing' && 'KI-Bewertung läuft...'}
            {status === 'idle' && `Zustandsbewertung starten (${images.length} Bilder)`}
          </button>
        </div>
      )}

      {/* Assessment Results */}
      {assessment && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-4">Bewertungsergebnis</h3>
          
          {/* Overall Grade */}
          <div className="bg-gray-50 rounded-lg p-6 mb-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getGradeColor(assessment.grade)}`}>
                  {assessment.grade}
                </span>
                <p className="text-2xl font-bold text-gray-800 mt-2">
                  {assessment.overall_score?.toFixed(1)}%
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">Vertrauen</p>
                <p className={`text-lg font-semibold ${getConfidenceColor(assessment.confidence)}`}>
                  {(assessment.confidence * 100)?.toFixed(1)}%
                </p>
              </div>
            </div>

            {assessment.manual_override && (
              <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4 mt-4">
                <p className="text-yellow-700 font-medium">Manuelle Übersteuerung aktiv</p>
                <p className="text-yellow-600 text-sm">{assessment.override_reason}</p>
              </div>
            )}
          </div>

          {/* Component Scores */}
          {assessment.component_scores && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              {Object.entries(assessment.component_scores).map(([component, score]) => (
                <div key={component} className="bg-white border rounded-lg p-4">
                  <h4 className="font-medium text-gray-700 capitalize mb-2">
                    {imageTypes.find(type => type.value === component)?.label || component}
                  </h4>
                  <div className="flex items-center">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 mr-3">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${score}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-600">
                      {score?.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Detailed Analysis */}
          {assessment.details && (
            <div className="bg-white border rounded-lg p-4 mb-4">
              <h4 className="font-medium text-gray-700 mb-3">Detailanalyse</h4>
              <div className="space-y-2">
                {Object.entries(assessment.details).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-gray-600 capitalize">
                      {key.replace(/_/g, ' ')}:
                    </span>
                    <span className="text-gray-800">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Manual Override Section */}
          <div className="border-t pt-4">
            {!manualOverride ? (
              <button
                onClick={() => setManualOverride(true)}
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                Bewertung manuell korrigieren
              </button>
            ) : (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-3">Manuelle Korrektur</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Neue Bewertung
                    </label>
                    <select
                      value={overrideGrade}
                      onChange={(e) => setOverrideGrade(e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                    >
                      <option value="">Bewertung auswählen</option>
                      {conditionGrades.map((grade) => (
                        <option key={grade.value} value={grade.value}>
                          {grade.label} - {grade.description}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Begründung
                    </label>
                    <textarea
                      value={overrideReason}
                      onChange={(e) => setOverrideReason(e.target.value)}
                      placeholder="Grund für die Korrektur..."
                      className="w-full border border-gray-300 rounded-md px-3 py-2 h-20"
                    />
                  </div>
                  <div className="flex space-x-3">
                    <button
                      onClick={handleManualOverride}
                      className="bg-orange-600 text-white px-4 py-2 rounded-md hover:bg-orange-700"
                    >
                      Korrektur anwenden
                    </button>
                    <button
                      onClick={() => setManualOverride(false)}
                      className="bg-gray-400 text-white px-4 py-2 rounded-md hover:bg-gray-500"
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
        <div className="bg-red-100 border-l-4 border-red-500 p-4 mb-4">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Status Display */}
      {status === 'assessing' && (
        <div className="bg-blue-100 border-l-4 border-blue-500 p-4">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-3"></div>
            <p className="text-blue-700">
              KI-basierte Zustandsbewertung wird durchgeführt...
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConditionAssessment;