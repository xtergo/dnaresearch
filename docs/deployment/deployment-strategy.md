# Deployment Strategy - DNA Research Platform

## Phase 1: MVP Deployment (Railway)

### Why Railway for MVP
- **Speed**: Repo → live app in under 30 minutes
- **Zero config**: Auto-detects Docker setup
- **All-in-one**: API + Postgres + Frontend in single platform
- **Free tier**: 1GB RAM, 500 hours/month - perfect for MVP
- **Real URLs**: Researchers get actual links to test

### MVP Deployment Steps
1. Connect Railway to GitHub repo
2. Deploy from `docker/docker-compose.yml`
3. Configure environment variables
4. Get public URL: `https://dnaresearch-production.up.railway.app`

### MVP Capabilities
- Interactive API documentation at `/docs`
- Theory validation and execution
- Small VCF file processing (demo datasets)
- 2-3 concurrent users for testing
- Perfect for researcher demos and feedback

### Cost: **$0/month**

---

## Phase 2: Production Migration (Fly.io + EU Infrastructure)

### When to Migrate
- MVP proves product-market fit
- Need EU data residency compliance
- Require larger storage and processing power
- Scale beyond 3-5 concurrent users

### Target Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Fly.io EU     │    │   Neon EU        │    │  Cloudflare R2  │
│   (API/App)     │◄──►│   (PostgreSQL)   │    │   (VCF Storage) │
│   2-8GB RAM     │    │   EU-West        │    │   EU Region     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Migration Benefits
- **EU compliance**: GDPR-compliant data residency
- **Cost efficiency**: Fly.io ~$2-8/month vs Railway $5-20/month
- **Scalability**: Better resource allocation
- **Storage**: Dedicated object storage for large VCF files
- **Performance**: EU-based infrastructure for European users

### Estimated Costs (Phase 2)
- **Fly.io API**: $2-8/month (1-4GB RAM)
- **Neon PostgreSQL**: $0-19/month (free tier → pro)
- **Cloudflare R2**: $0.015/GB storage + $0.36/million requests
- **Total**: ~$5-30/month depending on usage

---

## Migration Timeline

### Immediate (Week 1-2)
- [x] Deploy MVP on Railway free tier
- [ ] Get researcher feedback and usage patterns
- [ ] Document performance bottlenecks

### Short-term (Month 2-3)
- [ ] Monitor Railway resource usage
- [ ] Upgrade Railway if needed ($5-10/month)
- [ ] Plan EU compliance requirements

### Medium-term (Month 4-6)
- [ ] Migrate to Fly.io + Neon + R2 setup
- [ ] Implement EU data residency
- [ ] Scale based on user growth

---

## Decision Criteria

### Stay on Railway if:
- ✅ Usage stays under 1GB RAM
- ✅ No EU compliance requirements yet
- ✅ Fewer than 5 concurrent users
- ✅ Focus is on feature development over infrastructure

### Migrate to Fly.io if:
- ❌ Need more than 1GB RAM consistently
- ❌ EU data residency required
- ❌ Cost optimization needed (>$10/month)
- ❌ Custom infrastructure requirements

---

## Implementation Notes

### Railway Setup
```bash
# Connect repo and deploy
railway login
railway link
railway up
```

### Environment Variables (Railway)
```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
API_SECRET_KEY=...
```

### Future Fly.io Setup
```bash
# When migrating
fly launch
fly deploy
fly secrets set DATABASE_URL=...
```

---

## Success Metrics

### MVP Success (Railway)
- [ ] 10+ researcher signups
- [ ] 50+ theory validations
- [ ] 20+ theory executions
- [ ] Positive user feedback
- [ ] <2 second API response times

### Migration Triggers
- [ ] >80% RAM usage consistently
- [ ] EU compliance requirement
- [ ] >$15/month Railway costs
- [ ] >10 concurrent users

---

**Strategy Summary**: Start fast with Railway for MVP validation, migrate to cost-efficient EU-compliant infrastructure once proven.

**Last Updated**: 2025-01-XX  
**Next Review**: After MVP deployment and initial user feedback