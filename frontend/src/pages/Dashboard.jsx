export default function Dashboard() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">리뷰 대시보드</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">총 리뷰 수</p>
          <p className="text-3xl font-bold text-gray-800 mt-1">-</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">평균 별점</p>
          <p className="text-3xl font-bold text-gray-800 mt-1">-</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">미답변 리뷰</p>
          <p className="text-3xl font-bold text-gray-800 mt-1">-</p>
        </div>
      </div>
      <p className="text-gray-400 text-sm">Phase 2에서 리뷰 목록이 이곳에 표시됩니다.</p>
    </div>
  );
}
