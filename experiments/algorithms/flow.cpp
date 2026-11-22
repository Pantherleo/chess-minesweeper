#include <iostream>
#include <vector>
#include <queue>
#include <climits>
using namespace std;

int n;
vector<vector<int>> capacity;
vector<vector<int>> flow;

// Edmond–Karp Algorithm
int edmondKarp(int s, int t) {
    int totalFlow = 0;

    while (true) {
        vector<int> parent(n, -1);
        queue<int> q;

        q.push(s);
        parent[s] = s;

        // ----- BFS to find augmenting path -----
        while (!q.empty() && parent[t] == -1) {
            int u = q.front();
            q.pop();

            for (int v = 0; v < n; v++) {
                if (parent[v] == -1 && capacity[u][v] - flow[u][v] > 0) {
                    parent[v] = u;
                    q.push(v);
                }
            }
        }

        // No augmenting path
        if (parent[t] == -1)
            break;

        // ----- Find bottleneck -----
        int pathFlow = INT_MAX;
        int v = t;
        while (v != s) {
            int u = parent[v];
            pathFlow = min(pathFlow, capacity[u][v] - flow[u][v]);
            v = u;
        }

        // ----- Update flow -----
        v = t;
        while (v != s) {
            int u = parent[v];
            flow[u][v] += pathFlow;
            flow[v][u] -= pathFlow; // residual reverse edge
            v = u;
        }

        totalFlow += pathFlow;
        cout << "Augmenting path found, added flow = " << pathFlow << endl;
    }

    return totalFlow;
}

int main() {
    cout << "PART (i): Convert Undirected Graph to Flow Network\n";

    cout << "Enter number of nodes: ";
    cin >> n;

    int m;
    cout << "Enter number of edges: ";
    cin >> m;

    capacity.assign(n, vector<int>(n, 0));
    flow.assign(n, vector<int>(n, 0));

    cout << "\nEnter undirected edges (u v capacity)\n";

    for (int i = 0; i < m; i++) {
        int u, v, w;
        cin >> u >> v >> w;

        // Convert undirected → directed both ways
        capacity[u][v] += w;
        capacity[v][u] += w;

        cout << u << " -> " << v << " capacity = " << w << endl;
        cout << v << " -> " << u << " capacity = " << w << endl;
    }

    cout << "\nPART (ii): Edmond–Karp Max Flow\n";

    int s, t;
    cout << "Enter source node: ";
    cin >> s;

    cout << "Enter sink node: ";
    cin >> t;

    int maxFlow = edmondKarp(s, t);

    cout << "\nFinal Max Flow = " << maxFlow << endl;

    return 0;
}
