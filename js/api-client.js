/*
 * INPMS API 클라이언트 (점진적 전환 — 이중 쓰기)
 *
 * 동작 원리:
 *  - 부트 시 GET /api/export 로 서버 데이터 전체(첨부 포함)를 불러온다.
 *  - 서버가 응답하면 API 모드 ON. localStorage 는 오프라인 캐시로 계속 미러링.
 *  - 서버가 없거나(정적 배포/오프라인) 실패하면 API 모드 OFF → 기존 localStorage 동작 그대로.
 *  - saveData()/saveNewProducts() 가 호출되면 백그라운드로 변경분만 서버에 diff 동기화.
 *
 * 핵심: in-memory 배열(requests/newProducts)의 객체 형태를 바꾸지 않으므로
 *       기존 UI 코드(editItem/viewDetail/render 등)는 수정 불필요.
 */
(function () {
  function enc(s) { try { return encodeURIComponent(s || ''); } catch (e) { return ''; } }

  const Api = {
    base: '',
    enabled: false,
    reqSnap: new Map(),   // id -> JSON 문자열 (서버 반영 상태 스냅샷)
    npSnap: new Map(),
    _chain: {},           // 경로별 직렬화 큐 (동기화 레이스 방지)

    headers() {
      const p = (typeof profile !== 'undefined' && profile) ? profile : {};
      return {
        'Content-Type': 'application/json',
        'X-User-Name': enc(p.name),   // 한글 이름은 percent-encoding (서버에서 unquote)
        'X-User-Role': p.role || '',
        'X-User-Dept': p.dept || ''
      };
    },

    // 부트 로드: 성공 시 {requests, newProducts}, 실패(=정적/오프라인) 시 null
    async load() {
      try {
        const res = await fetch(this.base + '/api/export', { headers: { 'Accept': 'application/json' } });
        if (!res.ok) throw new Error('status ' + res.status);
        const data = await res.json();
        if (!data || !Array.isArray(data.data)) throw new Error('bad shape');
        const reqs = data.data;
        const nps = Array.isArray(data.newProducts) ? data.newProducts : [];
        this.enabled = true;
        this._snapshot(reqs, nps);
        return { requests: reqs, newProducts: nps };
      } catch (e) {
        this.enabled = false;
        return null;
      }
    },

    _snapshot(reqs, nps) {
      this.reqSnap = new Map(reqs.map(r => [r.id, JSON.stringify(r)]));
      this.npSnap = new Map(nps.map(n => [n.id, JSON.stringify(n)]));
    },

    syncRequests(arr) { return this._enqueue('/api/requests', arr, this.reqSnap); },
    syncNewProducts(arr) { return this._enqueue('/api/newproducts', arr, this.npSnap); },

    // 경로별로 순차 실행 (동시 saveData 호출 시 스냅샷 레이스 방지)
    _enqueue(path, arr, snap) {
      if (!this.enabled) return Promise.resolve();
      const prev = this._chain[path] || Promise.resolve();
      const next = prev.then(() => this._sync(path, arr, snap)).catch(() => {});
      this._chain[path] = next;
      return next;
    },

    async _sync(path, arr, snap) {
      const current = new Map((arr || []).filter(x => x && x.id).map(x => [x.id, x]));
      const tasks = [];
      // 신규/변경 → upsert
      for (const [id, obj] of current) {
        const json = JSON.stringify(obj);
        if (snap.get(id) !== json) {
          const exists = snap.has(id);
          tasks.push(this._upsert(path, id, obj, exists).then(() => snap.set(id, json)));
        }
      }
      // 사라진 id → delete
      for (const id of Array.from(snap.keys())) {
        if (!current.has(id)) {
          tasks.push(this._send('DELETE', path + '/' + id).then(() => snap.delete(id)));
        }
      }
      if (!tasks.length) return;
      const results = await Promise.allSettled(tasks);
      const failed = results.filter(r => r.status === 'rejected').length;
      if (failed) this._notifyError(failed);
    },

    async _upsert(path, id, obj, exists) {
      if (exists) return this._send('PUT', path + '/' + id, obj);
      try {
        return await this._send('POST', path, obj);
      } catch (e) {
        // 이미 존재(409)면 PUT 으로 폴백
        if (String(e.message || e).indexOf('409') >= 0) return this._send('PUT', path + '/' + id, obj);
        throw e;
      }
    },

    async _send(method, path, body) {
      const opt = { method: method, headers: this.headers() };
      if (body !== undefined) opt.body = JSON.stringify(body);
      const res = await fetch(this.base + path, opt);
      if (!res.ok && !(method === 'DELETE' && res.status === 404)) {
        throw new Error(method + ' ' + path + ' -> ' + res.status);
      }
      return res;
    },

    _notifyError(n) {
      try {
        if (typeof showSnackbar === 'function') {
          showSnackbar('⚠ 서버 동기화 일부 실패(' + n + '건). 로컬에는 저장됨 · 다음 저장 시 자동 재시도.');
        }
      } catch (e) { /* noop */ }
    }
  };

  window.INPMS_API = Api;
})();
