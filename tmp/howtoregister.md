사업주 페이지(https://pcmap.place.naver.com/hospital/{place_id}/review/visitor)에 리뷰 리스트의 각 리뷰에는 답글 button이 있고 

답글 버튼 셀렉터: 
#_review_list > li:nth-child(1) > div.pui__sRNfrm > div > a:nth-child(1)

답글 버튼 outerHTML
<a href="https://new-m.smartplace.naver.com/bizes/place-id/19528043/reviews/69a2637e2af664498c903d8a?from=search&amp;redirectUrl=https%3A%2F%2Fpcmap.place.naver.com%2Fhospital%2F19528043%2Freview%2Fvisitor" target="_blank" role="button" class="pui__i7LaW-" data-pui-click-code="reply"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 14 14" class="pui__OLlCAB" aria-hidden="true"><path fill-rule="evenodd" d="M7.415 1.923l3.54 3.554L3.552 13H0V9.435l7.415-7.512zM14 12.297V13H5.6v-.703H14zM10.335 0c1.384 0 2.51 1.156 2.51 2.546 0 .594-.21 1.17-.592 1.625l-.02.021-.783.788-3.54-3.554.785-.786C9.169.236 9.744 0 10.335 0z"></path></svg>답글</a>

답글 버튼을 클릭시 새탭에서 single_review_area.html이 포함된 리뷰 상세보기 페이지가 떠 

리뷰 상세보기 페이지에서 리뷰 영역의 답글 쓰기 버튼을 누르면 버튼이 textarea.html로 바뀌어 

이후 에 답글을 입력하고 등록을 클릭하면 댓글 등록이 완료돼