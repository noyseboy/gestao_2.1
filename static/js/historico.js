setTimeout(() => {
    document.querySelectorAll('.flash-center').forEach(el => {
        bootstrap.Alert.getOrCreateInstance(el).close();
    });
}, 3000);