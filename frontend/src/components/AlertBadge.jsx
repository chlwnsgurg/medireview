import { useEffect, useState } from 'react';
import { getUnreadCount } from '../api/client';

export default function AlertBadge() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    getUnreadCount()
      .then((res) => setCount(res.data.count))
      .catch(() => setCount(0));
  }, []);

  if (count === 0) return null;

  return (
    <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full">
      {count > 99 ? '99+' : count}
    </span>
  );
}
