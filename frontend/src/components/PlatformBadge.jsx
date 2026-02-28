const PLATFORM_LABELS = {
  naver: { label: '네이버', color: 'bg-green-100 text-green-700' },
  modudoc: { label: '모두닥', color: 'bg-blue-100 text-blue-700' },
  goodoc: { label: '굿닥', color: 'bg-purple-100 text-purple-700' },
};

export default function PlatformBadge({ platform }) {
  const info = PLATFORM_LABELS[platform] || { label: platform, color: 'bg-gray-100 text-gray-700' };

  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${info.color}`}>
      {info.label}
    </span>
  );
}
