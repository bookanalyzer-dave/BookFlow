import { useState, useEffect, useMemo } from 'react';
import { db } from '../firebaseConfig';
import { collection, onSnapshot, query, deleteDoc, doc } from 'firebase/firestore';
import { useAuth } from '../context/AuthContext';

export const useBooks = () => {
  const { currentUser } = useAuth();
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!currentUser) {
      setBooks([]);
      setLoading(false);
      return;
    }

    const collectionPath = `users/${currentUser.uid}/books`;
    const booksQuery = query(collection(db, collectionPath));

    const unsubscribe = onSnapshot(booksQuery, (querySnapshot) => {
      const booksData = querySnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data(),
      }));
      setBooks(booksData);
      setLoading(false);
    }, (err) => {
      console.error("Error fetching books:", err);
      setError("Fehler beim Laden der Bücher.");
      setLoading(false);
    });

    return () => unsubscribe();
  }, [currentUser]);

  const deleteBook = async (bookId) => {
    if (!currentUser) return;
    try {
      await deleteDoc(doc(db, `users/${currentUser.uid}/books`, bookId));
    } catch (err) {
      console.error("Delete error:", err);
      throw err;
    }
  };

  return { books, loading, error, deleteBook };
};
