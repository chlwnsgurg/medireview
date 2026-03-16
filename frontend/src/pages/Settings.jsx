import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  getHospital,
  createHospital,
  updateHospital,
  disconnectKakao,
  sendTestKakaoMessage,
} from '../api/client';

export default function Settings() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [form, setForm] = useState({
    name: '',
    naver_place_id: '',
    tone_style: 'polite',
    alert_threshold: 2,
  });
  const [kakaoState, setKakaoState] = useState({
    connected: false,
    notify_enabled: false,
  });
  const [isNew, setIsNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [kakaoMessage, setKakaoMessage] = useState('');
  const [kakaoLoading, setKakaoLoading] = useState(false);

  useEffect(() => {
    getHospital()
      .then((res) => {
        setForm(res.data);
        setKakaoState({
          connected: res.data.kakao_connected || false,
          notify_enabled: res.data.kakao_notify_enabled || false,
        });
      })
      .catch((err) => {
        if (err.response?.status === 404) setIsNew(true);
      });
  }, []);

  // 카카오 연동 콜백 처리
  useEffect(() => {
    if (searchParams.get('kakao') === 'connected') {
      setKakaoMessage('카카오 계정이 연동되었습니다.');
      setKakaoState((prev) => ({ ...prev, connected: true, notify_enabled: true }));
      searchParams.delete('kakao');
      setSearchParams(searchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

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

  const handleKakaoConnect = () => {
    window.location.href = '/api/kakao/authorize';
  };

  const handleKakaoDisconnect = async () => {
    if (!confirm('카카오 연동을 해제하시겠습니까?\n카카오톡 알림을 더 이상 받을 수 없습니다.')) return;
    setKakaoLoading(true);
    setKakaoMessage('');
    try {
      await disconnectKakao();
      setKakaoState({ connected: false, notify_enabled: false });
      setKakaoMessage('카카오 연동이 해제되었습니다.');
    } catch (err) {
      setKakaoMessage('연동 해제 실패: ' + (err.response?.data?.detail || err.message));
    } finally {
      setKakaoLoading(false);
    }
  };

  const handleKakaoToggle = async () => {
    const next = !kakaoState.notify_enabled;
    try {
      await updateHospital({ kakao_notify_enabled: next });
      setKakaoState((prev) => ({ ...prev, notify_enabled: next }));
    } catch (err) {
      setKakaoMessage('설정 변경 실패: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleTestMessage = async () => {
    setKakaoLoading(true);
    setKakaoMessage('');
    try {
      await sendTestKakaoMessage();
      setKakaoMessage('테스트 메시지가 발송되었습니다. 카카오톡을 확인해주세요.');
    } catch (err) {
      setKakaoMessage('발송 실패: ' + (err.response?.data?.detail || err.message));
    } finally {
      setKakaoLoading(false);
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
            반감 리뷰 알림
          </label>
          <p className="text-sm text-gray-500">
            리뷰 동기화 시 AI가 자동으로 리뷰 유형을 분류합니다.<br />
            <span className="text-orange-500 font-medium">컴플레인</span> 또는{' '}
            <span className="text-red-500 font-medium">클레임</span> 리뷰가 감지되면 알림이 생성됩니다.
          </p>
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

      {/* ── 카카오톡 알림 설정 ── */}
      <div className="bg-white rounded-lg shadow p-6 mt-6 space-y-5">
        <h3 className="text-lg font-bold text-gray-800">카카오톡 알림 설정</h3>

        {/* 연동 상태 */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">연동 상태:</span>
          {kakaoState.connected ? (
            <span className="text-sm font-medium text-green-600">✅ 연결됨</span>
          ) : (
            <span className="text-sm font-medium text-gray-400">❌ 미연결</span>
          )}
        </div>

        {!kakaoState.connected ? (
          /* 미연결 상태 */
          <div className="space-y-3">
            <button
              onClick={handleKakaoConnect}
              disabled={isNew}
              className="block"
            >
              <img
                src="//k.kakaocdn.net/14/dn/btqCn0WEmI3/nijroPfbpCa4at5EIsjyf0/o.jpg"
                alt="카카오 로그인"
                className="h-11 rounded hover:opacity-90 transition-opacity"
              />
            </button>
            {isNew && (
              <p className="text-xs text-red-400">
                병원 정보를 먼저 등록한 후 카카오 연동이 가능합니다.
              </p>
            )}
            <p className="text-xs text-gray-400">
              카카오 계정을 연동하면 반감 리뷰 감지 시 카카오톡으로 실시간 알림을 받을 수 있습니다.
            </p>
          </div>
        ) : (
          /* 연결됨 상태 */
          <div className="space-y-4">
            {/* 알림 ON/OFF 토글 */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">카카오톡 알림 받기</span>
              <button
                onClick={handleKakaoToggle}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  kakaoState.notify_enabled ? 'bg-yellow-400' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                    kakaoState.notify_enabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* 버튼 영역 */}
            <div className="flex gap-3">
              <button
                onClick={handleTestMessage}
                disabled={kakaoLoading || !kakaoState.notify_enabled}
                className="bg-yellow-400 text-gray-900 px-4 py-2 rounded-lg text-sm font-medium hover:bg-yellow-500 disabled:opacity-50 transition-colors"
              >
                {kakaoLoading ? '발송 중...' : '테스트 메시지 발송'}
              </button>
              <button
                onClick={handleKakaoDisconnect}
                disabled={kakaoLoading}
                className="border border-gray-300 text-gray-500 px-4 py-2 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                연동 해제
              </button>
            </div>

            <p className="text-xs text-gray-400">
              컴플레인/클레임 리뷰 감지, 자동 대응 보류, 승인 대기 알림이 카카오톡으로 전송됩니다.
            </p>
          </div>
        )}

        {/* 카카오 메시지 */}
        {kakaoMessage && (
          <p className={`text-sm ${
            kakaoMessage.includes('실패') ? 'text-red-500' : 'text-green-600'
          }`}>
            {kakaoMessage}
          </p>
        )}
      </div>
    </div>
  );
}
