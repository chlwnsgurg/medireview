지금 네이버 셀레니움을 이용한 네이버 comment_poster.py가 잘 작동하지 않아 다음과 같이 개선을 하고 싶어
1. 리뷰 ID 저장 후 리뷰 콘텐츠 매칭 시  사용

사업주 페이지(https://pcmap.place.naver.com/hospital/{place_id}/review/visitor)의 리뷰 리스트의 각 리뷰에는 답글 버튼이 있어 
각 리뷰는 review_element.html와 같이 구성되어 있어 

각 리뷰에는 아래와 같은 답글 버튼이 있어
<a href="https://new-m.smartplace.naver.com/bizes/place-id/19528043/reviews/69a6a9406063035997d2d22d?from=search&amp;redirectUrl=https%3A%2F%2Fpcmap.place.naver.com%2Fhospital%2F19528043%2Freview%2Fvisitor" target="_blank" role="button" class="pui__i7LaW-" data-pui-click-code="reply"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 14 14" class="pui__OLlCAB" aria-hidden="true"><path fill-rule="evenodd" d="M7.415 1.923l3.54 3.554L3.552 13H0V9.435l7.415-7.512zM14 12.297V13H5.6v-.703H14zM10.335 0c1.384 0 2.51 1.156 2.51 2.546 0 .594-.21 1.17-.592 1.625l-.02.021-.783.788-3.54-3.554.785-.786C9.169.236 9.744 0 10.335 0z"></path></svg>답글</a>

답글 버튼의 url에는 reviews다음에 review_id가 존재해
예를 들어 href="https://new-m.smartplace.naver.com/bizes/place-id/{place_}/reviews/69a6a9406063035997d2d22d?from=search&amp;redirectUrl=https%3A%2F%2Fpcmap.place.naver.com%2Fhospital%2F19528043%2Freview%2Fvisitor 에서 69a6a9406063035997d2d22d가 review_id야
