import { ID, validatePost } from '../lib/content.mjs';

const REPO = 'viral3on/modu-today';
class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}
export function createHandler(fetcher = fetch, environment = process.env) {
  return async function handler(req, res) {
    res.setHeader('Cache-Control', 'private, no-store');
    res.setHeader('X-Robots-Tag', 'noindex, nofollow');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    const send = (status, value) => res.status(status).json(value);
    try {
      if (req.method !== 'POST') { res.setHeader('Allow', 'POST'); throw new HttpError(405, '지원하지 않는 요청입니다.'); }
      const origins = ['https://modu.today', 'https://modu-today.vercel.app'];
      if (environment.VERCEL_URL) origins.push(`https://${environment.VERCEL_URL}`);
      if (environment.NODE_ENV !== 'production' && !environment.VERCEL) origins.push('http://localhost:4173', 'http://127.0.0.1:4173');
      if (!origins.includes(req.headers.origin)) throw new HttpError(403, '사이트 내부에서 다시 접속해 주세요.');
      if (!String(req.headers['content-type']).startsWith('application/json')) throw new HttpError(415, 'JSON 요청만 지원합니다.');
      const token = /^Bearer ([A-Za-z0-9_]{20,255})$/.exec(req.headers.authorization || '')?.[1];
      if (!token) throw new HttpError(401, '관리자 인증이 필요합니다.');
      if (Number(req.headers['content-length'] || 0) > 450000) throw new HttpError(413, '글이 너무 큽니다.');
      const body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
      if (!body || JSON.stringify(body).length > 150000) throw new HttpError(400, '요청 내용을 확인해 주세요.');
      const gh = async (path, options = {}) => {
        const response = await fetcher(`https://api.github.com${path}`, {
          ...options, signal: AbortSignal.timeout(15000),
          headers: {Accept:'application/vnd.github+json', Authorization:`Bearer ${token}`, 'X-GitHub-Api-Version':'2022-11-28', 'Content-Type':'application/json'}
        });
        if (response.status === 404 && options.optional) return null;
        if (!response.ok) {
          const status = response.status;
          if (status === 409 || status === 422) throw new HttpError(409, '다른 곳에서 글이 변경되었습니다. 초안을 내보낸 뒤 최신 글을 다시 불러와 주세요.');
          if (status === 401 || status === 403) throw new HttpError(status, '토큰 만료 또는 권한을 확인해 주세요. 이 저장소의 Contents 읽기·쓰기 권한이 필요합니다.');
          throw new HttpError(502, '저장소에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.');
        }
        return response.json();
      };
      // Checked on EVERY operation. Client-side hiding is not the security boundary.
      const repo = await gh(`/repos/${REPO}`);
      if (repo.permissions?.admin !== true || repo.archived) throw new HttpError(403, '저장소 관리자만 글을 관리할 수 있습니다.');
      const user = await gh('/user');
      if (!Number.isInteger(user.id)) throw new HttpError(403, '관리자 계정을 확인할 수 없습니다.');
      if (body.action === 'verify') return send(200, {ok:true, accountId:user.id});
      // Preview deployments never write into production accidentally.
      const branch = environment.VERCEL_ENV === 'preview' ? environment.VERCEL_GIT_COMMIT_REF : 'main';
      if (!branch || environment.VERCEL_ENV === 'preview' && branch === 'main') throw new HttpError(403, '미리보기 배포에서는 운영 글을 변경할 수 없습니다.');
      const base = `/repos/${REPO}/contents/content/posts`;
      if (body.action === 'list') {
        const files = await gh(`${base}?ref=${encodeURIComponent(branch)}`, {optional:true});
        return send(200, {posts:(files || []).filter(f=>f.type === 'file' && f.name.endsWith('.json')).map(f=>({id:f.name.slice(0,-5)}))});
      }
      if (!ID.test(body.id || '')) throw new HttpError(400, '글 식별자가 올바르지 않습니다.');
      const path = `${base}/${body.id}.json`;
      const existing = await gh(`${path}?ref=${encodeURIComponent(branch)}`, {optional:true});
      const previous = existing ? JSON.parse(Buffer.from(existing.content, 'base64').toString('utf8')) : null;
      if (body.action === 'load') {
        if (!existing) throw new HttpError(404, '글을 찾을 수 없습니다.');
        return send(200, {post:previous, sha:existing.sha});
      }
      if (body.action !== 'publish') throw new HttpError(400, '지원하지 않는 작업입니다.');
      if ((existing?.sha || null) !== (body.sha || null)) throw new HttpError(409, '저장소의 글이 변경되었습니다. 초안을 내보낸 뒤 다시 불러와 주세요.');
      let fields;
      try { fields = validatePost(body.post); } catch (error) { throw new HttpError(400, error.message); }
      const now = new Date().toISOString();
      const post = {...fields, id:body.id, status:'published', author:'MODU.TODAY 편집부', createdAt:previous?.createdAt || now, publishedAt:previous?.publishedAt || now, updatedAt:now};
      const result = await gh(path, {method:'PUT', body:JSON.stringify({
        message:`${existing ? 'Update' : 'Publish'} editorial article ${body.id}`,
        content:Buffer.from(JSON.stringify(post,null,2)+'\n').toString('base64'),
        branch, ...(existing ? {sha:existing.sha} : {}),
        author:{name:'MODU.TODAY',email:'editor@users.noreply.github.com'},
        committer:{name:'MODU.TODAY',email:'editor@users.noreply.github.com'}
      })});
      return send(200, {post, sha:result.content.sha, url:`/reading/${body.id}/`, commit:result.commit.sha, deployment:'pending'});
    } catch (error) {
      return send(error.status || 503, {error:error.status ? error.message : '요청을 처리하지 못했습니다. 초안은 유지됩니다. 잠시 후 다시 시도해 주세요.'});
    }
  };
}
export default createHandler();
