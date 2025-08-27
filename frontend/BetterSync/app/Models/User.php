<?php
// app/Models/User.php
namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens, Notifiable;

    protected $fillable = [
        'name', 'email', 'password', 'stripe_customer_id',
        'notion_access_token', 'google_access_token',
        'notion_refresh_token', 'google_refresh_token',
        'subscription_status', 'plan_type'
    ];

    protected $hidden = [
        'password', 'remember_token', 
        'notion_access_token', 'google_access_token',
        'notion_refresh_token', 'google_refresh_token'
    ];

    protected $casts = [
        'email_verified_at' => 'datetime',
        'password' => 'hashed',
    ];

    public function syncs()
    {
        return $this->hasMany(Sync::class);
    }

    public function isSubscribed()
    {
        return $this->subscription_status === 'active';
    }

    public function canCreateSync()
    {
        $limits = [
            'free' => 1,
            'starter' => 3,
            'pro' => 10,
            'business' => -1 // unlimited
        ];
        
        $current_count = $this->syncs()->count();
        $limit = $limits[$this->plan_type] ?? 0;
        
        return $limit === -1 || $current_count < $limit;
    }
}