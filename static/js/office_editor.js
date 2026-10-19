const editor = document.getElementById("onlyoffice-editor");
const errorMessage = document.getElementById("onlyoffice-error");
const editorConfig = JSON.parse(
    document.getElementById("onlyoffice-config").textContent,
);
const apiScript = document.createElement("script");

apiScript.src = editor.dataset.apiUrl;
apiScript.onload = () => {
    if (window.DocsAPI) {
        new window.DocsAPI.DocEditor(editor.id, editorConfig);
    } else {
        errorMessage.hidden = false;
    }
};
apiScript.onerror = () => {
    errorMessage.hidden = false;
};
document.head.appendChild(apiScript);
