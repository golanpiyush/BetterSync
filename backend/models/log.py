# # models/log.py  
# class SyncLog(db.Model):
#     __tablename__ = 'sync_logs'
    
#     id = db.Column(db.Integer, primary_key=True)
#     sync_id = db.Column(db.Integer, db.ForeignKey('syncs.id'), nullable=False)
    
#     # Log details
#     status = db.Column(db.String(50), nullable=False)  # started, completed, error
#     message = db.Column(db.Text)
#     rows_processed = db.Column(db.Integer, default=0)
#     errors = db.Column(db.JSON)
    
#     # Performance metrics
#     duration_seconds = db.Column(db.Float)
    
#     # Timestamp
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

#     def to_dict(self):
#         return {
#             'id': self.id,
#             'status': self.status,
#             'message': self.message,
#             'rows_processed': self.rows_processed,
#             'duration_seconds': self.duration_seconds,
#             'created_at': self.created_at.isoformat() if self.created_at else None
#         }