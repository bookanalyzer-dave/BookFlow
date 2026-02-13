import { useState, useEffect } from 'react';
import { db } from '../firebaseConfig';
import { doc, onSnapshot } from 'firebase/firestore';
import { useAuth } from '../context/AuthContext';

export const useConditionAssessment = (bookId) => {
  const { currentUser } = useAuth();
  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!bookId || !currentUser) {
      setAssessment(null);
      setLoading(false);
      return;
    }

    const assessmentRef = doc(db, 'users', currentUser.uid, 'condition_assessments', bookId);
    
    const unsubscribe = onSnapshot(assessmentRef, (docSnap) => {
      if (docSnap.exists()) {
        const data = docSnap.data();
        setAssessment(data);
      }
      setLoading(false);
    }, (err) => {
      console.error("Error fetching assessment:", err);
      setError("Fehler beim Laden der Zustandsbewertung.");
      setLoading(false);
    });

    return () => unsubscribe();
  }, [bookId, currentUser]);

  const assessCondition = async (images) => {
    if (!currentUser) return;
    try {
      const token = await currentUser.getIdToken();
      // ... API call logic ...
      // For now, I will extract this logic later if needed, but the main goal is data fetching.
      // I'll keep the API call logic in the component for now, or extract it if I have time.
      // Given the scope, I will extract the data fetching part first.
    } catch (err) {
      throw err;
    }
  };

  return { assessment, loading, error };
};
