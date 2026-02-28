const PLATFORMS = [
  { value: '', label: '전체 플랫폼' },
  { value: 'naver', label: '네이버' },
  { value: 'modudoc', label: '모두닥' },
  { value: 'goodoc', label: '굿닥' },
];

const RATINGS = [
  { value: '', label: '전체 별점' },
  { value: '5', label: '★ 5점' },
  { value: '4', label: '★ 4점' },
  { value: '3', label: '★ 3점' },
  { value: '2', label: '★ 2점' },
  { value: '1', label: '★ 1점' },
];

const SORTS = [
  { value: 'latest', label: '최신순' },
  { value: 'oldest', label: '오래된순' },
  { value: 'rating_high', label: '별점 높은순' },
  { value: 'rating_low', label: '별점 낮은순' },
];

export default function FilterBar({ filters, onChange }) {
  const handleChange = (key, value) => {
    onChange({ ...filters, [key]: value, page: 1 });
  };

  return (
    <div className="flex flex-wrap items-center gap-3 mb-6">
      {/* 플랫폼 */}
      <select
        value={filters.platform || ''}
        onChange={(e) => handleChange('platform', e.target.value)}
        className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {PLATFORMS.map((p) => (
          <option key={p.value} value={p.value}>{p.label}</option>
        ))}
      </select>

      {/* 별점 */}
      <select
        value={filters.rating || ''}
        onChange={(e) => handleChange('rating', e.target.value)}
        className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {RATINGS.map((r) => (
          <option key={r.value} value={r.value}>{r.label}</option>
        ))}
      </select>

      {/* 정렬 */}
      <select
        value={filters.sort || 'latest'}
        onChange={(e) => handleChange('sort', e.target.value)}
        className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {SORTS.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>

      {/* 답변 상태 */}
      <select
        value={filters.is_replied ?? ''}
        onChange={(e) => handleChange('is_replied', e.target.value)}
        className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">전체 상태</option>
        <option value="false">미답변</option>
        <option value="true">답변 완료</option>
      </select>
    </div>
  );
}
