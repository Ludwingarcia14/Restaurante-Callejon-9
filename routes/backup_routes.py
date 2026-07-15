from controllers.auth.AuthController import login_required, rol_required
from controllers.admin.BackupController import BackupController


def register_backup_routes(bp):

    @bp.route('/admin/backup', methods=['GET'])
    @login_required
    @rol_required(['1'])
    def admin_backup_view():
        return BackupController.index()

    @bp.route('/admin/backup/create', methods=['POST'])
    @login_required
    @rol_required(['1'])
    def admin_backup_create():
        return BackupController.create()

    @bp.route('/admin/backup/delete/<filename>', methods=['GET'])
    @login_required
    @rol_required(['1'])
    def admin_backup_delete(filename):
        return BackupController.delete_file(filename)

    @bp.route('/admin/backup/delete-with-auth/<filename>', methods=['POST'])
    @login_required
    @rol_required(['1'])
    def admin_backup_delete_with_auth(filename):
        return BackupController.delete_file_with_auth()

    @bp.route('/admin/backup/download-with-auth/<filename>', methods=['POST'])
    @login_required
    @rol_required(['1'])
    def admin_backup_download_with_auth(filename):
        return BackupController.download_with_auth()

    @bp.route('/admin/backup/restore', methods=['POST'])
    @login_required
    @rol_required(['1'])
    def admin_backup_restore():
        return BackupController.restore()

    @bp.route('/admin/backup/configure', methods=['POST'])
    @login_required
    @rol_required(['1'])
    def admin_backup_configure():
        return BackupController.configure_auto_backup()
