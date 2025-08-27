<?php
// app/Http/Controllers/DashboardController.php
namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use App\Services\ApiService;

class DashboardController extends Controller
{
    protected $apiService;

    public function __construct(ApiService $apiService)
    {
        $this->middleware('auth');
        $this->apiService = $apiService;
    }

    public function index()
    {
        $user = auth()->user();
        $syncs = $user->syncs()->with('logs')->latest()->get();
        
        $stats = [
            'total_syncs' => $syncs->count(),
            'active_syncs' => $syncs->where('status', 'active')->count(),
            'last_sync' => $syncs->where('last_sync', '!=', null)->max('last_sync'),
            'sync_limit' => $user->canCreateSync() ? 'available' : 'reached'
        ];

        return view('dashboard.index', compact('syncs', 'stats'));
    }

    public function connectNotion(Request $request)
    {
        $response = $this->apiService->post('/auth/notion', [
            'user_id' => auth()->id(),
            'redirect_uri' => route('dashboard.notion.callback')
        ]);

        return redirect($response['auth_url']);
    }

    public function connectGoogle(Request $request)
    {
        $response = $this->apiService->post('/auth/google', [
            'user_id' => auth()->id(),
            'redirect_uri' => route('dashboard.google.callback')
        ]);

        return redirect($response['auth_url']);
    }
}