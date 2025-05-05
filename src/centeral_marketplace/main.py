from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from injector import Injector
from .notifications.manager import manager
from .notifications.service import NotificationService
from .notifications.repository import NotificationRepository
from .products.service import ProductService
from .comments.service import CommentService
from .shared.interfaces import IProductService, ICommentService
import asyncio

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection setup
injector = Injector()

# Register services
injector.binder.bind(IProductService, to=ProductService)
injector.binder.bind(ICommentService, to=CommentService)
injector.binder.bind(NotificationRepository, to=NotificationRepository)
injector.binder.bind(NotificationService, to=NotificationService)

@app.on_event("startup")
async def startup():
    # Initialize notification service
    await manager.initialize()
    
    # Start listening for notifications in the background
    asyncio.create_task(manager.listen_for_notifications())

@app.on_event("shutdown")
async def shutdown():
    # Cleanup
    await manager.close()

@app.websocket("/api/v1/notifications/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: str = None, token: str = None):
    if not user_id and not token:
        await websocket.close(code=1008)  # Policy violation
        return
        
    # Use user_id directly for testing
    final_user_id = user_id or "test_user"  # Fallback for testing
    
    await manager.connect(websocket, final_user_id)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(final_user_id)

@app.get("/api/v1/health_check")
async def health_check():
    return {"status": "ok"} 