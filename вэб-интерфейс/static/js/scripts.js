const fileInput = document.getElementById('file-input');
const dragArea = document.getElementById('drag-area');

// Highlight drag area on drag over
dragArea.addEventListener('dragover', (event) => {
    event.preventDefault();
    dragArea.classList.add('hover');
});

// Remove highlight on drag leave
dragArea.addEventListener('dragleave', () => {
    dragArea.classList.remove('hover');
});

// Handle file drop
dragArea.addEventListener('drop', (event) => {
    event.preventDefault();
    dragArea.classList.remove('hover');
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files; // Assign dropped files to file input
    }
});

// Handle click on the drag area to open file dialog
dragArea.addEventListener('click', () => {
    fileInput.click();
});

// Update the drag area text when a file is selected via file input
fileInput.addEventListener('change', () => {
    const files = fileInput.files;
    if (files.length > 0) {
        dragArea.querySelector('p').textContent = `Файл выбран: ${files[0].name}`;
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.getElementById('hamburger');
    const mobileNav = document.getElementById('mobile-nav');

    hamburger.addEventListener('click', function() {
        mobileNav.classList.toggle('open'); // Переключаем класс для отображения/скрытия меню
    });
});