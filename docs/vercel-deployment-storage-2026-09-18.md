# Vercel 배포 저장 용량 관리 기록

- 프로젝트: `modu-today` / `viral3ons-projects` (Hobby)
- 2026-09-18 화면의 Deployment Storage 사용량: 15.75 GB / 10 GB. 이는 HTML 파일의 합계 크기와 같지 않습니다.
- 연결된 Vercel 배포 목록에서 매우 짧은 기간에 운영 배포가 반복 생성됐으며, 검증 문서와 GitHub Actions 설정 변경만 있는 커밋도 배포를 만들었습니다.
- `vercel.json`의 `ignoreCommand`는 이전 성공 배포와 현재 커밋을 비교해 `docs/`, `tests/`, `.github/` 및 Markdown 파일만 바뀌면 새 빌드를 건너뛰도록 설정했습니다. HTML, JSON 등 그 밖의 변경 또는 비교 실패 시에는 안전하게 배포합니다.
- 이 문서는 문서 변경만으로 새 배포가 생성되지 않는지 확인하는 회귀 테스트용 기록이기도 합니다.
- 기존 보관 배포본을 삭제하거나 요금제를 변경하지 않았습니다. 해당 저장 사용량이 감소했는지는 Vercel Usage에서 별도로 확인해야 합니다.
