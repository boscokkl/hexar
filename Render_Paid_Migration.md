# Render Paid Plan Upgrade Checklist

## **✅ Code Changes Required**

### **Backend Environment (.env)**
- [ ] Change `MESSAGE_BROKER_TYPE=memory` to `MESSAGE_BROKER_TYPE=redis`
- [ ] Update `REDIS_URL` to Render's Redis service URL
- [ ] Set `ENVIRONMENT=production`
- [ ] Update `CORS_ORIGINS` to your production frontend domain

### **Frontend Environment (.env.local)**
- [ ] Update `NEXT_PUBLIC_API_URL` to your Render backend URL
- [ ] Update `NEXT_PUBLIC_AGENT_WEBSOCKET_URL` to `wss://` (secure WebSocket)

## **🔧 Render Dashboard Configuration**

### **Add Redis Service**
- [ ] Add Redis add-on in Render dashboard
- [ ] Copy Redis connection URL to backend environment variables
- [ ] Verify Redis connectivity from your backend service

### **Enable Persistent Disk** 
- [ ] Attach persistent disk to backend service (optional, Redis handles persistence)
- [ ] Update any file-based caching paths if needed

### **Service Settings**
- [ ] Verify "Auto-Deploy" is enabled for zero-downtime deployments
- [ ] Set proper health check endpoints (`/health` in your FastAPI)
- [ ] Configure scaling settings (start with 1 instance)

## **🚀 Deployment Steps**
- [ ] Deploy backend with Redis configuration
- [ ] Deploy frontend with production API URLs
- [ ] Test agent WebSocket connections
- [ ] Verify cache persistence after service restart
- [ ] Monitor agent response times (should be consistently fast)

## **⚠️ Critical Benefits You'll Get**
- **No Cold Starts**: Agents respond in 2-3s instead of 15-30s
- **Persistent Cache**: Your 30-day static analysis cache survives restarts
- **Zero Downtime**: Updates don't interrupt user conversations
- **Better Resources**: Handle concurrent users without memory issues

Your codebase is already production-ready - just needs Redis enabled and environment variables updated for Render's managed services.