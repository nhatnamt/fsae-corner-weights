// import Sortable from 'sortablejs';

function getBoxBoundingRect(box) {
    let width = box.width;
    let length = box.length;
    if (box.angle === 90) {
      width = box.length;
      length = box.width;
    }
    const top_left = { x: box.x - width / 2, y: box.y - length / 2 };
    const bot_right = { x: box.x + width / 2, y: box.y + length / 2 };
    return { top_left, bot_right };
  }
  
  export default {
    template: `
      <div>
        <canvas id="canvas" width="400" height="920"></canvas>
      </div>`,

  
    methods: {  
      clearCanvas(cxt) {
        cxt.clearRect(0, 0, cxt.canvas.width, cxt.canvas.height);
      },

      update() {
        const ctx = this.ctx;
        this.clearCanvas(ctx);
        this.drawCar(true);

        const { startX, startY } = this.getCarPosition();
        // this.drawCOG(ctx, startX + 33.5, startY + 343.5); fl
        // this.drawCOG(ctx, startX + 332.5, startY + 775); // rr
        console.log(this.l2r_ratio, this.f2r_ratio);
        this.drawCOG(ctx, startX + 33.5 + (332.5-33.5)*this.l2r_ratio, startY + 343.5+ (775-343.5)*this.f2r_ratio); // fr
      },
      getCarPosition() {
        const startX = (this.canvas.width - this.carWidth) / 2;
        const startY = (this.canvas.height - this.carLength) / 2;
        return { startX, startY };
      },

      drawCOG(ctx, x, y) {
        ctx.beginPath();
        ctx.arc(x, y, 7, 0, 2 * Math.PI);
        ctx.fillStyle = 'red';
        ctx.fill();
      },
  
      /* -------------------------------------------------------------------------- */
      /*                               DRAW CAR                                */
      /* -------------------------------------------------------------------------- */
      drawCar(forceRedraw = false, useOffscreenCanvas = false) {
        const width = this.carWidth;
        const length = this.carLength;
        if (!this.imgCache) {
          this.imgCache = new Image();
          this.imgCache.onload = () => this.drawCar(width, length, true, useOffscreenCanvas);
          this.imgCache.src = '/assets/TS_23.svg';
          return;
        }
        if (!forceRedraw && !this.imgCache.complete && !useOffscreenCanvas) return;
  
        const ctx = this.ctx;
        const { startX, startY } = this.getCarPosition();
  
        ctx.drawImage(this.imgCache, startX, startY, width, length);
      },
    },
  
    mounted() {
      this.canvas = this.$el.querySelector('#canvas');
      this.ctx = this.canvas.getContext('2d');
      
      // set width and height of canvas of parent element
      this.canvas.width = this.$el.clientWidth;
      this.canvas.height = this.$el.clientHeight;
      this.carWidth = 366.32;
      this.carLength = 900;
      this.update();
    },
  
    props: {
      f2r_ratio: Number,
      l2r_ratio: Number,
    },
  };
  