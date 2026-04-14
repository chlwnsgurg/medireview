import { useEffect, useState } from 'react';
import { getUnreadCount } from '@medireview/api/client';

export default function AlertBadge() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const fetch = () =>
      getUnreadCount()
        .then((res) => setCount(res.data.count))
        .catch(() => setCount(0));
    fetch();
    const id = setInterval(fetch, 60000);
    return () => clearInterval(id);
  }, []);

  if (count === 0) return null;

  return (
    <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full">
      {count > 99 ? '99+' : count}
    </span>
  );
}
