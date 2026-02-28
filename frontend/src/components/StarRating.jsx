export default function StarRating({ rating, scale = 5 }) {
  // scale이 10이면 5점 기준으로 변환
  const normalized = scale === 10 ? rating / 2 : rating;
  const full = Math.floor(normalized);
  const half = normalized - full >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);

  return (
    <span className="inline-flex items-center gap-0.5 text-sm">
      {Array.from({ length: full }, (_, i) => (
        <span key={`f${i}`} className="text-yellow-400">★</span>
      ))}
      {half && <span className="text-yellow-400">★</span>}
      {Array.from({ length: empty }, (_, i) => (
        <span key={`e${i}`} className="text-gray-300">★</span>
      ))}
      <span className="ml-1 text-gray-500 text-xs">{rating}</span>
    </span>
  );
}
