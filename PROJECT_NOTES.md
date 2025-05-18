# Project Status & Open Points

_Last updated: 2025-05-18_

## ✅ What is working
- **User authentication (OAuth2 code flow) with REST API:**
  - Able to authenticate as a user and successfully call Power BI REST API endpoints (e.g., list workspaces).

## ⚠️ What is under investigation / Not yet working
- **Service principal (app registration) authentication:**
  - REST API: 401 Unauthorized when calling admin endpoints (likely due to propagation delay or config).
  - pyadomd (XMLA): 403 Forbidden when connecting with service principal token.
  - Recent changes: Security group created, app added, group enabled for admin API access (may need more time to propagate).

## 📝 Next Steps / Open Points
- [ ] Wait and re-test REST API with service principal after propagation.
- [ ] Re-test pyadomd connection after propagation.
- [ ] If issues persist, double-check group membership, workspace type (Premium/Fabric), and admin portal settings.
- [ ] Document any further troubleshooting or successful tests here.

---

**Tip:** Update this file after every major test or config change. This way, you (or anyone else) will always know what was working, what was not, and what was tried!
