import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os

fig, ax = plt.subplots(1, 1, figsize=(28, 20))
ax.set_xlim(0, 28)
ax.set_ylim(0, 20)
ax.axis('off')
fig.patch.set_facecolor('#F5F5F5')

def draw_box(ax, x, y, w, h, text, color='#2196F3', text_color='white', fontsize=9, bold=False, alpha=0.95):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                         facecolor=color, edgecolor='#555', linewidth=1.2, alpha=alpha)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    ax.text(x + w/2, y + h/2, text, ha='center', va='center',
            fontsize=fontsize, color=text_color, fontweight=weight,
            fontfamily='sans-serif', linespacing=1.35)

def draw_arrow(ax, x1, y1, x2, y2, color='#666', lw=1.5, text='', rad=0.05):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                               connectionstyle=f"arc3,rad={rad}"))
    if text:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my+0.2, text, ha='center', va='center', fontsize=7, color=color,
                fontweight='bold', fontfamily='sans-serif',
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor=color, alpha=0.9))

def draw_section(ax, x, y, w, h, title, color):
    sec = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor='white', edgecolor=color, linewidth=2.5, alpha=0.4)
    ax.add_patch(sec)
    bar = FancyBboxPatch((x, y+h-0.55), w, 0.55, boxstyle="round,pad=0.05",
                         facecolor=color, edgecolor='none', alpha=0.9)
    ax.add_patch(bar)
    ax.text(x+w/2, y+h-0.27, title, ha='center', va='center',
            fontsize=12, color='white', fontweight='bold', fontfamily='sans-serif')

# ==================== TITLE ====================
ax.text(14, 19.5, 'SO DO HE THONG - CAU TRUC NGINX & DOCKER',
        ha='center', fontsize=20, fontweight='bold', color='#1565C0', fontfamily='sans-serif')
ax.text(14, 19.1, 'Phan biet Nginx trong Docker Container vs Nginx tren Host Server',
        ha='center', fontsize=11, color='#888', fontfamily='sans-serif')

# ==================== INTERNET ====================
draw_section(ax, 0.5, 17.0, 27, 1.8, 'INTERNET', '#FF6F00')
draw_box(ax, 1.0, 17.2, 5, 1.0, 'User mo trinh duyet\ngo quock6.click', '#FFF3E0', '#E65100', 9)
draw_box(ax, 6.5, 17.2, 5, 1.0, 'DNS quock6.click\n-> IP Server VPS', '#FFE0B2', '#BF360C', 9)
draw_box(ax, 12.0, 17.2, 5, 1.0, 'HTTP Request\nGET /, POST /auth/...', '#FFF3E0', '#E65100', 9)
draw_arrow(ax, 6.0, 17.7, 6.5, 17.7, '#E65100', 1.5)
draw_arrow(ax, 11.5, 17.7, 12.0, 17.7, '#E65100', 1.5)

# Arrow from Internet to Host Nginx
draw_arrow(ax, 14.5, 17.2, 14.5, 16.5, '#D32F2F', 2.5, text='Port 80')

# ==================== HOST SERVER ====================
draw_section(ax, 0.5, 10.0, 27, 6.3, 'SERVER VPS - quock6.click (Ubuntu/Debian)', '#D32F2F')

# Nginx Host
draw_box(ax, 1.0, 14.2, 12, 1.8, '', '#FFCDD2', '#C62828', 9)
ax.text(7, 15.7, 'NGINX TREN HOST SERVER', ha='center', fontsize=11, fontweight='bold',
        color='#C62828', fontfamily='sans-serif')
ax.text(7, 15.25, 'File: deploy/quock6.click.conf', ha='center', fontsize=8, color='#888', fontfamily='sans-serif')
ax.text(7, 14.8, 'Lang nghe port 80 | domain: quock6.click', ha='center', fontsize=9, color='#333', fontfamily='sans-serif')
ax.text(7, 14.4, 'Reverse proxy: / -> :3100 | /auth/ -> :8081 | /ws/ -> :8081', ha='center', fontsize=8, color='#555', fontfamily='sans-serif')

# Docker containers area
draw_box(ax, 14.0, 11.5, 13.0, 4.5, '', '#E3F2FD', '#1565C0', 9)
ax.text(20.5, 15.7, 'DOCKER CONTAINERS', ha='center', fontsize=11, fontweight='bold',
        color='#1565C0', fontfamily='sans-serif')

# Container boxes
# MySQL
draw_box(ax, 14.3, 14.3, 3.8, 1.0, 'MySQL 8.0\n:3306 (internal)\nmysql-data volume', '#C8E6C9', '#2E7D32', 8)
# ActiveMQ
draw_box(ax, 18.3, 14.3, 3.8, 1.0, 'ActiveMQ 5.15\n:61616 (internal)\nactivemq-data volume', '#C8E6C9', '#2E7D32', 8)
# Backend
draw_box(ax, 14.3, 12.8, 3.8, 1.2, 'Backend Spring Boot\n:8080 (internal)\n-> :8081 (host)\nupload-data volume', '#BBDEFB', '#1565C0', 8)
# Frontend with Nginx inside
draw_box(ax, 18.3, 12.8, 8.2, 1.2, '', '#FFF3E0', '#E65100', 8)
ax.text(22.4, 13.7, 'Frontend React + NGINX TRONG DOCKER', ha='center', fontsize=8, fontweight='bold',
        color='#E65100', fontfamily='sans-serif')
ax.text(22.4, 13.2, 'nginx.conf (trong container)', ha='center', fontsize=7, color='#888', fontfamily='sans-serif')
ax.text(22.4, 12.9, ':80 (internal) -> :3100 (host)', ha='center', fontsize=7, color='#555', fontfamily='sans-serif')

# Arrows: Host Nginx -> Containers
draw_arrow(ax, 13.0, 15.1, 14.3, 14.8, '#C62828', 1.5, text='/  ->  :3100')
draw_arrow(ax, 13.0, 14.7, 14.3, 13.4, '#C62828', 1.5, text='/auth/ -> :8080')

# Internal arrow: Frontend Nginx -> Backend
draw_arrow(ax, 18.3, 13.4, 18.1, 13.4, '#FF9800', 1.2, text='proxy_pass\nhttp://backend:8080', rad=0)

# Backend -> MySQL
draw_arrow(ax, 16.2, 12.8, 16.2, 15.3, '#1565C0', 1.2, text='JDBC', rad=-0.15)

# ==================== DOCKER COMPOSE ====================
draw_section(ax, 0.5, 8.0, 12.7, 1.8, 'DOCKER COMPOSE', '#2E7D32')
compose_text = (
    "docker-compose.yml:\n"
    "- 4 services: mysql, activemq, backend, frontend\n"
    "- 4 named volumes: mysql-data, activemq-data, activemq-log, upload-data\n"
    "- depends_on: backend cho MySQL healthy"
)
draw_box(ax, 1.0, 8.1, 11.7, 1.2, compose_text, '#E8F5E9', '#1B5E20', 8)

# ==================== CI/CD ====================
draw_section(ax, 14.0, 8.0, 13.5, 1.8, 'CI/CD - GITHUB ACTIONS', '#00897B')
cicd_text = (
    "deploy.yml: push to main -> Build -> Test -> Deploy\n"
    "SSH vao server: git pull -> docker compose down -> docker compose up -d --build\n"
    "Secrets: SERVER_HOST, SERVER_USER, SERVER_SSH_KEY"
)
draw_box(ax, 14.5, 8.1, 12.5, 1.2, cicd_text, '#E0F2F1', '#00695C', 8)

# ==================== COMPARISON TABLE ====================
draw_section(ax, 0.5, 4.5, 27, 3.2, 'SO SANH 2 LOP NGINX', '#7B1FA2')

# Nginx Host
draw_box(ax, 1.0, 4.7, 12.5, 2.5, '', '#F3E5F5', '#7B1FA2', 9)
ax.text(7.25, 6.95, 'NGINX TREN HOST SERVER', ha='center', fontsize=10, fontweight='bold',
        color='#7B1FA2', fontfamily='sans-serif')
host_lines = [
    'File: deploy/quock6.click.conf',
    'Vi tri: /etc/nginx/sites-enabled/',
    'Lang nghe: port 80 (HTTP)',
    'Chuc nang: Reverse proxy tu Internet vao Docker',
    'Routes: /auth/, /oauth2/, /room/, /ws/, ...',
    'Khong co gzip, khong cache static'
]
for i, line in enumerate(host_lines):
    ax.text(1.5, 6.5 - i*0.3, f'• {line}', fontsize=8, color='#333', fontfamily='sans-serif')

# Nginx Container
draw_box(ax, 14.5, 4.7, 12.5, 2.5, '', '#FFF3E0', '#E65100', 9)
ax.text(20.75, 6.95, 'NGINX TRONG DOCKER CONTAINER', ha='center', fontsize=10, fontweight='bold',
        color='#E65100', fontfamily='sans-serif')
container_lines = [
    'File: rent-manager-app/nginx.conf',
    'Vi tri: /etc/nginx/conf.d/default.conf (trong container)',
    'Lang nghe: port 80 (internal, map ra 3100)',
    'Chuc nang: Serve React SPA + proxy noi bo',
    'Gzip: nen CSS, JS, JSON, SVG',
    'Cache: /static/ 1 nam, hinh 30 ngay, font 1 nam',
    'SPA fallback: try_files $uri $uri/ /index.html',
    'WebSocket: proxy_pass backend:8080/ws/'
]
for i, line in enumerate(container_lines):
    ax.text(15.0, 6.5 - i*0.28, f'• {line}', fontsize=8, color='#333', fontfamily='sans-serif')

# ==================== REQUEST FLOW ====================
draw_section(ax, 0.5, 1.5, 27, 2.7, 'LUU QUY TRINH REQUEST', '#1565C0')

steps = [
    ('1', 'User go\nquock6.click', '#BBDEFB'),
    ('2', 'DNS giai\nIP server', '#C8E6C9'),
    ('3', 'Host Nginx\n:80 nhan request', '#FFCDD2'),
    ('4', 'Route / -> Frontend:3100\nRoute /auth/ -> Backend:8081', '#FFF9C4'),
    ('5', 'Frontend Nginx\ngzip + cache + SPA', '#FFE0B2'),
    ('6', 'Backend xu ly\ntra JSON', '#E1BEE7'),
    ('7', 'User nhan\ntrang web', '#E8F5E9'),
]
for i, (num, text, color) in enumerate(steps):
    x = 1.0 + i * 3.8
    draw_box(ax, x, 1.7, 3.3, 2.0, f'{num}. {text}', color, '#333', 8, True)
    if i < len(steps) - 1:
        draw_arrow(ax, x+3.3, 2.7, x+3.8, 2.7, '#555', 1.5)

# ==================== LEGEND ====================
legend_y = 0.3
legend_items = [
    ('#1565C0', 'Developer/GitHub'),
    ('#D32F2F', 'Host Server (Nginx)'),
    ('#E65100', 'Docker Container (Nginx)'),
    ('#2E7D32', 'Docker Compose'),
    ('#00897B', 'CI/CD Pipeline'),
    ('#7B1FA2', 'So sanh 2 lop Nginx'),
]
for i, (color, label) in enumerate(legend_items):
    x = 2 + i * 4.3
    box = FancyBboxPatch((x, legend_y), 0.35, 0.35, boxstyle="round,pad=0.05",
                         facecolor=color, edgecolor='none', alpha=0.85)
    ax.add_patch(box)
    ax.text(x + 0.5, legend_y + 0.17, label, ha='left', va='center', fontsize=8, color='#333', fontfamily='sans-serif')

plt.tight_layout(pad=0.3)
output = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SoDoNginx_Docker.png')
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='#F5F5F5')
plt.close()
print(f'Da tao so do tai: {output}')
