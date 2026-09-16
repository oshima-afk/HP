// 施工実績のデータ。1件 = 1つのオブジェクト。
// 追加するときは works 配列の先頭に足すと、ページの上に出ます。
//   id       … 写真枠を区別するための文字列（重複しないこと）
//   category … "new" | "repair" | "etc" | "asbestos"
//   image    … 写真のURL。空文字なら編集画面でドラッグ＆ドロップできる枠になります
export const categories = [
  { id: "new",      label: "新築塗装",                kicker: "New build" },
  { id: "repair",   label: "修繕工事",                kicker: "Repair" },
  { id: "etc",      label: "その他",                  kicker: "Other" },
  { id: "asbestos", label: "アスベスト（石綿）除去工事", kicker: "Asbestos" },
];

export const works = [
  { id: "w-2025-01", category: "repair",   title: "マンション大規模修繕",        place: "戸田市",             year: "2025年", detail: "全48戸／外壁改修・シーリング打ち替え・屋上防水", image: "" },
  { id: "w-2025-02", category: "new",      title: "新築戸建の外部塗装",          place: "さいたま市中央区",   year: "2025年", detail: "窯業系サイディング／シリコン塗装",               image: "" },
  { id: "w-2025-03", category: "etc",      title: "屋上ウレタン防水",            place: "蕨市",               year: "2025年", detail: "工場屋上／通気緩衝工法",                         image: "" },
  { id: "w-2025-04", category: "asbestos", title: "石綿含有仕上塗材の除去",      place: "さいたま市南区",     year: "2025年", detail: "事前調査・届出のうえ湿式工法で除去",             image: "" },
  { id: "w-2024-01", category: "new",      title: "新築アパートの外壁・鉄部塗装", place: "戸田市",             year: "2024年", detail: "全8戸／鉄部下地処理を含む",                     image: "" },
  { id: "w-2024-02", category: "repair",   title: "アパート外部改修",            place: "朝霞市",             year: "2024年", detail: "全12戸／外壁塗装・鉄部階段の補修",               image: "" },
  { id: "w-2024-03", category: "etc",      title: "鉄部塗装",                    place: "蕨市",               year: "2024年", detail: "工場外階段および手すり",                         image: "" },
  { id: "w-2024-04", category: "asbestos", title: "石綿含有スレート屋根の改修",  place: "川口市",             year: "2024年", detail: "飛散防止措置・法令に基づく処分",                 image: "" },
  { id: "w-2024-05", category: "new",      title: "新築店舗の内外装塗装",        place: "東京都板橋区",       year: "2024年", detail: "木部・軒天・内壁の仕上げ",                       image: "" },
  { id: "w-2024-06", category: "asbestos", title: "事前調査のみのご依頼",        place: "戸田市",             year: "2024年", detail: "有資格者による調査と報告書の作成",               image: "" },
  { id: "w-2023-01", category: "repair",   title: "戸建住宅の塗り替え",          place: "川口市",             year: "2023年", detail: "築28年／外壁・屋根塗装",                         image: "" },
  { id: "w-2023-02", category: "etc",      title: "美容室の内装塗装",            place: "東京都板橋区",       year: "2023年", detail: "営業時間外の夜間施工",                           image: "" },
];
