/* static/js/mesero-charts.js
   Tema único de Chart.js para todas las gráficas del mesero.
   Cargar DESPUÉS de chart.js y ANTES de los scripts de cada vista. */

(function () {
  const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

  window.C9Charts = {
    get palette() {
      return [css('--bar-1'), css('--bar-2'), css('--bar-3'), css('--bar-4'), css('--bar-5')];
    },
    get clusters() {
    return { VIP: '#f59e0b', Regular: '#3b82f6', Ocasional: '#94a3b8' };
    },

    /* Aplica el tema global. Llamar una vez al cargar la página. */
    theme() {
      const C = window.Chart;
      C.defaults.font.family = "'Instrument Sans', system-ui, sans-serif";
      C.defaults.font.size = 12;
      C.defaults.color = css('--ink-3');
      C.defaults.borderColor = css('--line-soft');
      C.defaults.plugins.legend.labels.usePointStyle = true;
      C.defaults.plugins.legend.labels.boxWidth = 8;
      C.defaults.plugins.legend.labels.padding = 16;
      C.defaults.plugins.tooltip.backgroundColor = css('--surface');
      C.defaults.plugins.tooltip.titleColor = css('--ink');
      C.defaults.plugins.tooltip.bodyColor = css('--ink-2');
      C.defaults.plugins.tooltip.borderColor = css('--line');
      C.defaults.plugins.tooltip.borderWidth = 1;
      C.defaults.plugins.tooltip.padding = 12;
      C.defaults.plugins.tooltip.displayColors = false;
      C.defaults.elements.bar.borderRadius = 4;
      C.defaults.elements.bar.borderSkipped = 'bottom';
      C.defaults.elements.line.tension = 0.3;
      C.defaults.elements.point.radius = 0;
      C.defaults.maintainAspectRatio = false;
    },

    /* Ejes limpios: sin rejilla vertical, sin borde de eje. */
    axes(opts = {}) {
      return {
        x: { grid: { display: false }, border: { display: false }, ...(opts.x || {}) },
        y: { grid: { color: css('--line-soft') }, border: { display: false },
             ticks: { padding: 8 }, ...(opts.y || {}) }
      };
    },

    money(n) {
      return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(n || 0);
    },

    /* Barras con la barra máxima destacada (propinas por hora, demanda por día) */
    bars(canvas, labels, data, { highlightMax = true, money = false } = {}) {
      const max = Math.max(...data);
      const colors = data.map(v => (highlightMax && v === max) ? css('--bar-1') : css('--bar-5'));
      return new Chart(canvas, {
        type: 'bar',
        data: { labels, datasets: [{ data, backgroundColor: colors }] },
        options: {
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: c => money ? this.money(c.parsed.y) : c.parsed.y } }
          },
          scales: this.axes({ y: { beginAtZero: true, ticks: { callback: v => money ? this.money(v) : v } } })
        }
      });
    },

    /* Scatter de K-Means / Random Forest, un dataset por cluster */
    scatter(canvas, grupos, { xLabel = 'PC1', yLabel = 'PC2' } = {}) {
      const c = this.clusters;
      return new Chart(canvas, {
        type: 'scatter',
        data: {
          datasets: Object.entries(grupos).map(([nombre, puntos]) => ({
            label: nombre,
            data: puntos,
            backgroundColor: (c[nombre] || css('--ink-3')) + 'cc',
            borderColor: c[nombre] || css('--ink-3'),
            pointRadius: 8,
            pointHoverRadius: 11
          }))
        },
        options: {
          plugins: {
            legend: { position: 'bottom' },
            tooltip: { callbacks: { label: ctx => `${ctx.dataset.label} · ${ctx.raw.mesa || ''}` } }
          },
          scales: this.axes({
            x: { title: { display: true, text: xLabel, color: css('--ink-3') } },
            y: { title: { display: true, text: yLabel, color: css('--ink-3') } }
          })
        }
      });
    }
  };

  document.addEventListener('DOMContentLoaded', () => window.Chart && window.C9Charts.theme());
})();
