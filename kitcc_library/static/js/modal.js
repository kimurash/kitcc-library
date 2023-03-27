const modal = document.getElementById('modal');
const openButton = document.getElementById('modal-open');
const closeButton = document.getElementById('modal-close');

const closeModal = () => {
    document.body.style.overflow = '';
    modal.style.display = 'none';
    Quagga.stop();
}

openButton.addEventListener('click', () => {
    document.body.style.overflow = 'hidden'; // はみ出した部分は非表示
    modal.style.display = 'block';

    Quagga.init({
        locate: true, // バーコードの位置を自動検出する
        inputStream: {
            type: 'LiveStream',
            constraints: {
                width: window.innerWidth, // ウィンドウいっぱいに表示
                facingMode: 'environment' // 背面カメラを使用
            },
        },
        decoder: {
            readers: [{
                format: 'ean_reader', // 読み取るバーコードの種類
                config: {},
            }],
        },
        locator: {
            halfSample: true,
        }},
        (err) => {
            if (!err) {
                Quagga.start();
            } else {
                closeModal()
                window.console.error(err)
                // 画面上部にポップアップを表示
                alert('この機能を利用するには\nブラウザのカメラ利用を許可してください');
            }
        }
    );
});

closeButton.addEventListener('click', () => {
    closeModal()
});

Quagga.onDetected((result) => {
    /* 認識したコードを表示 */
    const code = result.codeResult.code;
    document.getElementById('ISBN').value = code;
    closeModal()
});
