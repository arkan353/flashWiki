// Centralized frontend API functions using axios
const api = (function(){
    const client = axios.create();

    function handleError(err){
        if(err && err.response && err.response.data) return err.response.data;
        return {success:false, message: err.message || 'Unknown error'};
    }

    function notify(message, type='info'){
        const el = document.getElementById('notify');
        if(!el) return console.log(type, message);
        el.textContent = message;
        el.className = 'notify '+type;
        setTimeout(()=>{ el.textContent=''; el.className='notify'; }, 4000);
    }

    // Auth
    async function login(email, password){
        try{ const r = await client.post('/api/login', {email, password}); return r.data; }catch(e){ return handleError(e); }
    }
    async function logout(){ try{ const r = await client.get('/api/logout'); return r.data;}catch(e){ return handleError(e);} }
    async function register(name,email,password){ try{ const r = await client.post('/api/register',{name,email,password}); return r.data;}catch(e){ return handleError(e);} }
    async function getProfile(){ try{ const r = await client.get('/api/user/profile'); return r.data;}catch(e){ return handleError(e);} }

    // Articles
    async function getArticles(){ try{ const r = await client.get('/api/articles'); return r.data;}catch(e){ return handleError(e);} }
    async function getArticle(id){ try{ const r = await client.get('/api/articles/'+id); return r.data;}catch(e){ return handleError(e);} }
    async function createArticle(payload){ // payload: {title,content,tags,cover_image,organization_id,chart_id}
        try{ const r = await client.post('/api/articles', payload); return r.data;}catch(e){ return handleError(e);} }
    async function getSandbox(){ try{ const r = await client.get('/api/articles/sandbox'); return r.data;}catch(e){ return handleError(e);} }
    async function approveArticle(articleId){ try{ const r = await client.post(`/api/articles/${articleId}/approve`); return r.data;}catch(e){ return handleError(e);} }

    // Ratings
    async function rateArticle(articleId, score){ try{ const r = await client.post(`/api/articles/${articleId}/rate`, {score}); return r.data;}catch(e){ return handleError(e);} }
    async function removeRating(articleId){ try{ const r = await client.delete(`/api/articles/${articleId}/rate`); return r.data;}catch(e){ return handleError(e);} }
    async function getRating(articleId){ try{ const r = await client.get(`/api/articles/${articleId}/rating`); return r.data;}catch(e){ return handleError(e);} }

    // Tags / Orgs
    async function getTags(){ try{ const r = await client.get('/api/tags'); return r.data;}catch(e){ return handleError(e);} }
    async function createTag(name){ try{ const r = await client.post('/api/tags', {name}); return r.data;}catch(e){ return handleError(e);} }
    async function getOrgs(){ try{ const r = await client.get('/api/organizations'); return r.data;}catch(e){ return handleError(e);} }
    async function createOrg(payload){ try{ const r = await client.post('/api/organizations', payload); return r.data;}catch(e){ return handleError(e);} }

    // Upload image (multipart/form-data)
    async function uploadImage(file){
        try{
            const fd = new FormData();
            fd.append('file', file);
            const r = await client.post('/api/upload_image', fd, { headers: {'Content-Type':'multipart/form-data'} });
            return r.data;
        }catch(e){ return handleError(e);}    
    }

    return {
        notify,
        login, logout, register, getProfile,
        getArticles, getArticle, createArticle, getSandbox, approveArticle,
        rateArticle, removeRating, getRating,
        getTags, createTag, getOrgs, createOrg,
        uploadImage
    };
})();

// Expose to global for easy use in inline scripts
window.api = api;
