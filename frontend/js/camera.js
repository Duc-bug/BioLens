class BioLensCamera {
    constructor(videoEl, canvasEl, onPhotoCaptured) {
        this.videoEl = videoEl;
        this.canvasEl = canvasEl;
        this.onPhotoCaptured = onPhotoCaptured;
        this.stream = null;
        this.facingMode = "environment"; // Ưu tiên camera sau khi mở trên điện thoại
    }

    async start() {
        this.stop();
        const constraints = {
            video: {
                facingMode: { ideal: this.facingMode },
                width: { ideal: 1280 },
                height: { ideal: 960 },
            },
            audio: false,
        };
        try {
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.videoEl.srcObject = this.stream;
            await this.videoEl.play();
            return true;
        } catch (err) {
            // Dự phòng nếu thiết bị chỉ có 1 webcam mặc định
            try {
                this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                this.videoEl.srcObject = this.stream;
                await this.videoEl.play();
                return true;
            } catch (fallbackErr) {
                alert("Không thể truy cập Camera. Vui lòng cấp quyền Camera trên trình duyệt hoặc dùng nút 'Tải ảnh từ máy'.");
                return false;
            }
        }
    }

    async switchCamera() {
        this.facingMode = this.facingMode === "environment" ? "user" : "environment";
        return await this.start();
    }

    captureFrame() {
        if (!this.stream) return;
        const w = this.videoEl.videoWidth || 640;
        const h = this.videoEl.videoHeight || 480;
        this.canvasEl.width = w;
        this.canvasEl.height = h;
        const ctx = this.canvasEl.getContext("2d");
        ctx.drawImage(this.videoEl, 0, 0, w, h);

        this.canvasEl.toBlob(
            (blob) => {
                if (!blob) return;
                const file = new File([blob], `biolens_capture_${Date.now()}.jpg`, {
                    type: "image/jpeg",
                });
                const dataUrl = this.canvasEl.toDataURL("image/jpeg", 0.92);
                this.stop();
                if (this.onPhotoCaptured) {
                    this.onPhotoCaptured(file, dataUrl);
                }
            },
            "image/jpeg",
            0.92
        );
    }

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach((t) => t.stop());
            this.stream = null;
        }
        if (this.videoEl) {
            this.videoEl.srcObject = null;
        }
    }
}

window.BioLensCamera = BioLensCamera;
