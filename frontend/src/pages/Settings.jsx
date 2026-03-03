import { useEffect, useState } from 'react';
import { getHospital, createHospital, updateHospital } from '../api/client';

export default function Settings() {
  const [form, setForm] = useState({
    name: '',
    naver_place_id: '',
    tone_style: 'polite',
    alert_threshold: 2,
  });
  const [isNew, setIsNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    getHospital()
      .then((res) => setForm(res.data))
      .catch((err) => {
        if (err.response?.status === 404) setIsNew(true);
      });
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: name === 'alert_threshold' ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');

    try {
      if (isNew) {
        await createHospital(form);
        setIsNew(false);
        setMessage('병원 정보가 등록되었습니다.');
      } else {
        await updateHospital(form);
        setMessage('설정이 저장되었습니다.');
      }
    } catch (err) {
      setMessage('저장 실패: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-xl">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">병원 설정</h2>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
        {/* 병원명 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            병원명
          </label>
          <input
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            placeholder="예: 장생한의원"
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* 네이버 지도 Place ID */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            네이버 지도 Place ID
          </label>
          <input
            type="text"
            name="naver_place_id"
            value={form.naver_place_id || ''}
            onChange={handleChange}
            placeholder="예: 19528043"
            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-xs text-gray-400 mt-1">
            네이버 지도 URL에서 hospital/ 뒤의 숫자입니다. (예: pcmap.place.naver.com/hospital/<b>19528043</b>)
          </p>
        </div>

        {/* 톤앤매너 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            AI 댓글 톤앤매너
          </label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="tone_style"
                value="polite"
                checked={form.tone_style === 'polite'}
                onChange={handleChange}
                className="text-blue-600"
              />
              <span className="text-sm text-gray-700">정중한 말투</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="tone_style"
                value="friendly"
                checked={form.tone_style === 'friendly'}
                onChange={handleChange}
                className="text-blue-600"
              />
              <span className="text-sm text-gray-700">친근한 말투</span>
            </label>
          </div>
        </div>

        {/* 알림 기준 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            저평점 알림 기준 (5점 만점)
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              name="alert_threshold"
              value={form.alert_threshold}
              onChange={handleChange}
              min={1}
              max={5}
              className="w-20 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <span className="text-sm text-gray-500">점 이하 리뷰 시 알림</span>
          </div>
        </div>

        {/* 저장 버튼 */}
        <div className="flex items-center gap-4">
          <button
            type="submit"
            disabled={saving}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {saving ? '저장 중...' : isNew ? '등록' : '저장'}
          </button>
          {message && (
            <span className={`text-sm ${message.includes('실패') ? 'text-red-500' : 'text-green-600'}`}>
              {message}
            </span>
          )}
        </div>
      </form>
    </div>
  );
}
