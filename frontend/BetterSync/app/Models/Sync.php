<?php
// app/Models/Sync.php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Sync extends Model
{
    protected $fillable = [
        'user_id', 'name', 'notion_database_id', 'sheet_id',
        'mapping', 'filters', 'frequency', 'last_sync',
        'status', 'sync_direction'
    ];

    protected $casts = [
        'mapping' => 'array',
        'filters' => 'array',
        'last_sync' => 'datetime'
    ];

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function logs()
    {
        return $this->hasMany(SyncLog::class);
    }
}